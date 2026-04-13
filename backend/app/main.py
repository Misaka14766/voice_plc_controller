import asyncio
import logging
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(ROOT_DIR)

from backend.config.settings import settings
from backend.core import get_asr, get_tts, get_llm, get_plc
from backend.core.llm.openai_llm import set_plc_instance
from backend.core.template_matcher import TemplateMatcher
from backend.utils.audio_recorder import AudioRecorder
from backend.utils.key_trigger import KeyTrigger
from backend.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class VoiceApp:
    def __init__(self):
        self.asr = get_asr()
        self.tts = get_tts()
        self.llm = get_llm()
        self.plc = get_plc()
        set_plc_instance(self.plc)

        if self.asr:
            self.asr.set_callback(self._on_asr_result)
            self.asr.start()

        self.recorder = AudioRecorder()
        self.is_listening = False
        self.loop = None

        self.conversation_history = []
        self.max_history_turns = 10

        self.template_matcher = None

        # 键盘触发器（如果 PLC 未启用或未配置触发变量时使用）
        self.trigger = KeyTrigger(
            on_press=self.start_listening,
            on_release=self.stop_listening,
            trigger_key=settings.ASR_TRIGGER_KEY
        )

        # PLC 连接
        if self.plc:
            if self.plc.connect():
                logger.info("✅ PLC 连接成功")
                self.template_matcher = TemplateMatcher(self.plc)
                self._setup_plc_monitors()
                self.plc.start_monitoring()  # 启动统一的监控线程
            else:
                logger.warning("⚠️ PLC 连接失败，将使用键盘触发")

        # 运行时语音开关（由配置和控制台命令控制）
        self.runtime_voice_input_enabled = settings.VOICE_INPUT_ENABLED
        self.runtime_voice_output_enabled = settings.VOICE_OUTPUT_ENABLED

    def _setup_plc_monitors(self):
        """配置PLC监控组"""
        from backend.core.plc.base import MonitorGroup, TriggerMode

        # 1. 默认变量监控组（持续显示）
        vars_to_monitor = settings.monitor_variables
        if vars_to_monitor:
            group = MonitorGroup(
                group_id="default_display",
                variables=vars_to_monitor,
                callback=lambda vals: logger.debug(f"监控值: {vals}"),
                mode=TriggerMode.ALWAYS,
                interval_ms=settings.MONITOR_INTERVAL_MS
            )
            self.plc.add_monitor_group(group)

        # 2. 语音触发变量监控组（变化时触发）
        trigger_var = settings.PLC_TRIGGER_VAR
        if trigger_var:
            group = MonitorGroup(
                group_id="voice_trigger",
                variables=[(trigger_var, "BOOL")],
                callback=self._on_trigger_changed,
                mode=TriggerMode.ON_CHANGE,
                interval_ms=50
            )
            self.plc.add_monitor_group(group)
            logger.info(f"已注册触发变量监控: {trigger_var} (变化触发)")

    def _on_trigger_changed(self, values: dict):
        """触发变量变化回调，在监控线程中调用"""
        trigger_var = settings.PLC_TRIGGER_VAR
        current_state = values.get(trigger_var, False)
        self.start_listening() if current_state else self.stop_listening()

    def _on_asr_result(self, text: str, is_final: bool):
        """ASR 识别结果回调"""
        if is_final:
            logger.info(f"ASR 最终结果: {text}")
            asyncio.run_coroutine_threadsafe(self._handle_input_text(text), self.loop)
        else:
            sys.stdout.write(f"\r(实时) {text}  ")
            sys.stdout.flush()

    def start_listening(self):
        if not self.is_listening and self.runtime_voice_input_enabled:
            self.is_listening = True
            self.asr.reset()
            self.recorder.start()
            logger.info("🎤 录音中...")

    def stop_listening(self):
        if self.is_listening:
            self.is_listening = False
            self.recorder.stop()
            logger.info("🔇 录音结束")
            if self.asr:
                asyncio.run_coroutine_threadsafe(self._send_final_chunk(), self.loop)

    async def _send_final_chunk(self):
        self.asr.feed_chunk(b'', is_final=True)

    async def _handle_input_text(self, text: str):
        text = text.strip()
        if not text:
            return
        if text.startswith('/'):
            await self._handle_command(text[1:].strip())
            return
        logger.info(f"输入: {text}")
        if text.lower() in ("退出", "quit", "exit"):
            logger.info("收到退出命令")
            self.running = False
            return
        # 模板匹配
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
        # LLM
        self.conversation_history.append({"role": "user", "content": text})
        if len(self.conversation_history) > self.max_history_turns * 2:
            self.conversation_history = self.conversation_history[-self.max_history_turns * 2:]
        messages = [{"role": m["role"], "content": m["content"]} for m in self.conversation_history]
        response = await self.llm.generate(messages=messages)
        logger.info(f"LLM: {response.content}")
        self.conversation_history.append({"role": "assistant", "content": response.content})
        await self._output_response(response.content)

    async def _handle_command(self, cmd: str):
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
                            self.asr.start()
                        print("✅ 语音输入已开启")
                    elif val in ("off", "false", "0"):
                        self.runtime_voice_input_enabled = False
                        if self.asr:
                            self.asr.stop()
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
        if self.runtime_voice_output_enabled:
            await self.tts.speak(text)
        print(f"\n🤖 助手: {text}\n")

    async def audio_consumer(self):
        """将音频数据送入 ASR"""
        while self.running:
            if self.is_listening and self.runtime_voice_input_enabled:
                chunk = self.recorder.get_chunk(timeout=0.1)
                if chunk:
                    self.asr.feed_chunk(chunk, is_final=False)
            else:
                await asyncio.sleep(0.1)

    async def console_input_loop(self):
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

        # 如果未使用 PLC 触发，则启动键盘监听
        if not (settings.PLC_ENABLED and self.plc and settings.PLC_TRIGGER_VAR):
            self.trigger.start()
            logger.info(f"按下 '{settings.ASR_TRIGGER_KEY}' 键开始说话，松开结束。")
        else:
            logger.info("使用 PLC 触发变量控制录音，键盘监听已禁用。")

        tasks = [
            asyncio.create_task(self.audio_consumer()),
            asyncio.create_task(self.console_input_loop()),
        ]

        print("📝 控制台输出已启用")

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            self.running = False
            if not (settings.PLC_ENABLED and self.plc and settings.PLC_TRIGGER_VAR):
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