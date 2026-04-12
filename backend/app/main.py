import asyncio
import logging
import sys
from typing import Optional

from backend.config.settings import settings
from backend.core import get_asr, get_tts, get_llm, get_plc
from backend.core.llm.openai_llm import set_plc_instance
from backend.core.template_matcher import TemplateMatcher
from backend.utils.audio_recorder import AudioRecorder
from backend.utils.key_trigger import KeyTrigger
from backend.utils.logger import setup_logging

# 初始化彩色日志
setup_logging()
logger = logging.getLogger(__name__)


class VoiceApp:
    def __init__(self):
        self.asr = get_asr()
        self.tts = get_tts()
        self.llm = get_llm()
        self.plc = get_plc()
        set_plc_instance(self.plc)

        # 设置 ASR 回调
        if self.asr:
            self.asr.set_callback(self._on_asr_result)
            self.asr.start()

        self.recorder = AudioRecorder()
        self.is_pressed = False
        self.partial_text = ""
        self.loop = None

        self.conversation_history = []
        self.max_history_turns = 10

        self.template_matcher = None

        # 键盘触发器
        self.trigger = KeyTrigger(
            on_press=self.on_press,
            on_release=self.on_release,
            trigger_key=settings.TRIGGER_KEY
        )

        # PLC 连接
        if self.plc:
            if self.plc.connect():
                logger.info("✅ PLC 连接成功")
                self.template_matcher = TemplateMatcher(self.plc)
                self._start_default_monitoring()
            else:
                logger.warning("⚠️ PLC 连接失败，将使用模拟数据")

        # 运行时配置（可动态修改）
        self.runtime_voice_input_enabled = settings.VOICE_INPUT_ENABLED
        self.runtime_voice_output_enabled = settings.VOICE_OUTPUT_ENABLED

        # 控制台输入任务
        self.console_task: Optional[asyncio.Task] = None

    def _start_default_monitoring(self):
        vars_to_monitor = settings.monitor_variables
        if vars_to_monitor:
            def monitor_callback(values):
                logger.debug(f"监控值: {values}")
            self.plc.start_monitoring(
                variables=vars_to_monitor,
                callback=monitor_callback,
                interval_ms=settings.MONITOR_INTERVAL_MS
            )
            logger.info(f"已启动默认监控，变量数量: {len(vars_to_monitor)}")

    def _on_asr_result(self, text: str, is_final: bool):
        """ASR 识别结果回调（可能在异步线程中调用）"""
        if is_final:
            logger.info(f"ASR 最终结果: {text}")
            # 将处理任务安全地投递到主事件循环
            asyncio.run_coroutine_threadsafe(self._handle_final_result(text), self.loop)
        else:
            # 实时显示中间结果
            self.partial_text = text
            sys.stdout.write(f"\r(实时) {text}  ")
            sys.stdout.flush()

    async def _handle_final_result(self, text: str):
        """处理最终识别结果（在主事件循环中执行）"""
        self.partial_text = text
        await self._handle_input_text(text)

    def on_press(self):
        if not self.is_pressed and self.runtime_voice_input_enabled:
            self.is_pressed = True
            self.partial_text = ""
            self.asr.reset()
            self.recorder.start()
            logger.info("🎤 录音中...")

    def on_release(self):
        if self.is_pressed:
            self.is_pressed = False
            self.recorder.stop()
            logger.info("🔇 录音结束")
            # 发送结束标志给 ASR
            if self.asr:
                # 需要在事件循环中执行，避免阻塞回调
                asyncio.run_coroutine_threadsafe(self._send_final_chunk(), self.loop)

    async def _send_final_chunk(self):
        """发送空数据通知 ASR 流结束"""
        self.asr.feed_chunk(b'', is_final=True)

    async def _handle_input_text(self, text: str):
        """统一处理输入文本（语音识别结果或控制台输入）"""
        text = text.strip()
        if not text:
            return

        # 控制台命令检测（以 '/' 开头）
        if text.startswith('/'):
            await self._handle_command(text[1:].strip())
            return

        logger.info(f"输入: {text}")

        # 退出命令（普通文本方式也支持）
        if text.lower() in ("退出", "quit", "exit"):
            logger.info("收到退出命令")
            self.running = False
            return

        # ---------- 模板匹配快速通道 ----------
        if settings.USE_TEMPLATE_MATCHING and self.template_matcher:
            match_result = self.template_matcher.match(text)
            if match_result:
                op_type, params = match_result
                response_text = self.template_matcher.execute(op_type, params)
                logger.info(f"模板命中: {op_type} -> {response_text}")
                self.conversation_history.append({"role": "user", "content": text})
                self.conversation_history.append({"role": "assistant", "content": response_text})
                await self._output_response(response_text)
                return

        # ---------- LLM 处理 ----------
        self.conversation_history.append({"role": "user", "content": text})
        if len(self.conversation_history) > self.max_history_turns * 2:
            self.conversation_history = self.conversation_history[-self.max_history_turns * 2:]

        messages = [{"role": m["role"], "content": m["content"]} for m in self.conversation_history]
        response = await self.llm.generate(messages=messages)

        logger.info(f"LLM: {response.content}")
        self.conversation_history.append({"role": "assistant", "content": response.content})
        await self._output_response(response.content)

    async def _handle_command(self, cmd: str):
        """处理控制台命令"""
        parts = cmd.split()
        if not parts:
            return
        command = parts[0].lower()

        if command == "help" or command == "?":
            print("""
可用命令：
  /voice input on/off     - 开启/关闭语音输入
  /voice output on/off    - 开启/关闭语音输出
  /voice status           - 查看当前语音状态
  /volume [0.0-1.0]       - 设置或查看音量
  /stop                   - 停止当前播放
  /plc status             - 查看PLC连接状态
  /clear                  - 清空对话历史
  /exit 或 /quit          - 退出程序
  /help                   - 显示帮助
            """)
        elif command == "voice":
            if len(parts) < 2:
                print("用法: /voice <input|output|status> [on|off]")
                return
            subcmd = parts[1].lower()
            if subcmd == "input":
                if len(parts) >= 3:
                    val = parts[2].lower()
                    if val in ("on", "true", "1"):
                        self.runtime_voice_input_enabled = True
                        if self.asr:
                            self.asr.start()  # 启动长连接
                        print("✅ 语音输入已开启")
                    elif val in ("off", "false", "0"):
                        self.runtime_voice_input_enabled = False
                        if self.asr:
                            self.asr.stop()  # 关闭长连接
                        print("🔇 语音输入已关闭")
                    else:
                        print("无效参数，请使用 on 或 off")
                else:
                    print(f"语音输入状态: {'开启' if self.runtime_voice_input_enabled else '关闭'}")
            elif subcmd == "output":
                if len(parts) >= 3:
                    val = parts[2].lower()
                    if val in ("on", "true", "1"):
                        self.runtime_voice_output_enabled = True
                        print("✅ 语音输出已开启")
                    elif val in ("off", "false", "0"):
                        self.runtime_voice_output_enabled = False
                        print("🔇 语音输出已关闭")
                    else:
                        print("无效参数，请使用 on 或 off")
                else:
                    print(f"语音输出状态: {'开启' if self.runtime_voice_output_enabled else '关闭'}")
            elif subcmd == "status":
                print(f"语音输入: {'开启' if self.runtime_voice_input_enabled else '关闭'}")
                print(f"语音输出: {'开启' if self.runtime_voice_output_enabled else '关闭'}")
            else:
                print("未知子命令，支持: input, output, status")
        elif command == "volume":
            if len(parts) >= 2:
                try:
                    vol = float(parts[1])
                    self.tts.set_volume(vol)
                    print(f"🔊 音量已设置为 {vol:.1%}")
                except ValueError:
                    print("无效音量值，请输入 0.0 ~ 1.0 之间的数字")
            else:
                print(f"当前音量: {self.tts.get_volume():.1%}")
        elif command == "stop":
            self.tts.stop()
            print("⏹️ 播放已停止")
        elif command == "plc":
            if len(parts) < 2:
                print("用法: /plc status")
                return
            subcmd = parts[1].lower()
            if subcmd == "status":
                if self.plc:
                    status = "已连接" if self.plc.is_connected() else "未连接"
                    print(f"PLC 状态: {status}")
                else:
                    print("PLC 未启用")
        elif command == "clear":
            self.conversation_history.clear()
            print("✅ 对话历史已清空")
        elif command in ("exit", "quit"):
            print("正在退出...")
            self.running = False
        else:
            print(f"未知命令: {command}，输入 /help 查看帮助")

    async def _output_response(self, text: str):
        """根据运行时配置输出响应"""
        if self.runtime_voice_output_enabled:
            await self.tts.speak(text)
        # 控制台输出始终开启
        print(f"\n🤖 助手: {text}\n")

    async def audio_consumer(self):
        """实时将音频数据送入 ASR（流式）"""
        while self.running:
            if self.is_pressed and self.runtime_voice_input_enabled:
                chunk = self.recorder.get_chunk(timeout=0.1)
                if chunk:
                    # 实时喂入音频数据，不等待最终结果
                    self.asr.feed_chunk(chunk, is_final=False)
            else:
                await asyncio.sleep(0.1)

    async def plc_trigger_monitor(self):
        """PLC 触发监听（需同时启用 PLC 和语音输入）"""
        if not settings.PLC_ENABLED or not self.plc or not self.plc.is_connected():
            return
        trigger_var = settings.PLC_TRIGGER_VAR
        last_state = False
        while self.running:
            if not self.runtime_voice_input_enabled:
                await asyncio.sleep(0.1)
                continue
            try:
                current_state = self.plc.read_bool(trigger_var)
                if current_state and not last_state:
                    self.on_press()
                elif not current_state and last_state:
                    self.on_release()
                last_state = current_state
            except Exception as e:
                logger.error(f"PLC 轮询错误: {e}")
            await asyncio.sleep(0.05)

    async def console_input_loop(self):
        """控制台输入循环（始终开启）"""
        print("\n💬 控制台已就绪，输入 '/' 查看命令，直接输入文字对话")
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                text = await loop.run_in_executor(None, sys.stdin.readline)
                if text:
                    await self._handle_input_text(text)
            except EOFError:
                break
            except Exception as e:
                logger.error(f"控制台输入错误: {e}")

    async def run(self):
        self.running = True
        self.loop = asyncio.get_running_loop()

        # 启动按键监听
        self.trigger.start()
        logger.info(f"按下 '{settings.TRIGGER_KEY}' 键开始说话，松开结束。")

        tasks = [
            asyncio.create_task(self.audio_consumer()),
            asyncio.create_task(self.console_input_loop()),
        ]
        if settings.PLC_ENABLED and self.plc:
            tasks.append(asyncio.create_task(self.plc_trigger_monitor()))

        print("📝 控制台输出已启用")

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            self.running = False
            self.trigger.stop()
            self.recorder.close()
            if self.asr:
                self.asr.stop()
            if self.plc:
                self.plc.stop_monitoring()
                self.plc.disconnect()
            logger.info("程序已退出")


if __name__ == "__main__":
    app = VoiceApp()
    asyncio.run(app.run())