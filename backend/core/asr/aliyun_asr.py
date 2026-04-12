import threading
import queue
import time
import json
import logging
from typing import Optional, Callable

import nls

from .base import BaseASR
from .aliyun_token import AliyunTokenManager
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class AliyunASR(BaseASR):
    """阿里云实时语音识别（长连接模式，支持静音保活）"""

    def __init__(self):
        self.appkey = settings.ALIYUN_ASR_APPKEY
        self.url = settings.ALIYUN_ASR_URL

        if settings.ALIYUN_AK_ID and settings.ALIYUN_AK_SECRET:
            self._token_manager = AliyunTokenManager(
                access_key_id=settings.ALIYUN_AK_ID,
                access_key_secret=settings.ALIYUN_AK_SECRET,
                region=settings.ALIYUN_ASR_REGION,
            )
            self._use_dynamic_token = True
        else:
            self._static_token = settings.ALIYUN_ASR_TOKEN
            self._use_dynamic_token = False
            self._token_manager = None

        self._callback: Optional[Callable[[str, bool], None]] = None
        self._sr: Optional[nls.NlsSpeechTranscriber] = None
        self._audio_queue = queue.Queue()
        self._send_thread: Optional[threading.Thread] = None
        self._final_text = ""
        self._is_ready = False
        self._is_running = False
        self._stop_sending = False

        nls.enableTrace(False)
        logger.info(f"阿里云 ASR 初始化完成，URL: {self.url}")

    def _get_token(self) -> str:
        if self._use_dynamic_token and self._token_manager:
            return self._token_manager.get_token()
        return self._static_token

    def set_callback(self, callback: Optional[Callable[[str, bool], None]] = None):
        self._callback = callback

    def start(self):
        """启动识别会话（全局仅调用一次）"""
        if self._is_running:
            return

        token = self._get_token()
        if not token:
            logger.error("无法获取阿里云 Token")
            return

        self._is_ready = False
        self._stop_sending = False
        self._final_text = ""
        self._audio_queue = queue.Queue()

        self._sr = nls.NlsSpeechTranscriber(
            url=self.url,
            token=token,
            appkey=self.appkey,
            on_start=self._on_start,
            on_sentence_begin=self._on_sentence_begin,
            on_sentence_end=self._on_sentence_end,
            on_result_changed=self._on_result_changed,
            on_completed=self._on_completed,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._sr.start(
            aformat="pcm",
            enable_intermediate_result=True,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True,
        )

        # 等待连接就绪
        timeout = 5
        while not self._is_ready and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1

        if not self._is_ready:
            logger.error("阿里云 ASR 连接超时")
            self._sr = None
            return

        self._is_running = True
        self._send_thread = threading.Thread(target=self._send_audio_loop, daemon=True)
        self._send_thread.start()
        logger.info("阿里云 ASR 长连接已建立")

    def stop(self):
        """关闭长连接"""
        if not self._is_running:
            return

        self._is_running = False
        self._stop_sending = True

        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=2.0)

        if self._sr:
            try:
                # 发送结束指令并停止
                self._sr.ctrl(ex={"test": "end"})
                time.sleep(0.2)
                self._sr.stop(timeout=5)
            except Exception as e:
                logger.error(f"停止 ASR 出错: {e}")
            self._sr = None

        self._is_ready = False
        logger.info("阿里云 ASR 长连接已关闭")

    def feed_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """喂入音频数据，is_final 仅表示本次说话的结束（不是关闭连接）"""
        if not self._is_ready:
            return ""
        if chunk:
            self._audio_queue.put(chunk)
        if is_final:
            # 发送一个标志表示说话结束，但我们不关闭连接，只是暂停发送音频
            self._audio_queue.put(b"__END__")
        return ""

    def reset(self):
        """重置内部状态（例如每次开始说话前清空缓冲区）"""
        self._final_text = ""
        # 不重置连接

    # ---------- 回调 ----------
    def _parse_message(self, message):
        if isinstance(message, dict):
            return message
        if isinstance(message, str):
            try:
                return json.loads(message)
            except json.JSONDecodeError:
                return {}
        return {}

    def _on_start(self, message, *args):
        self._is_ready = True
        logger.info(f"识别已就绪: {self._parse_message(message)}")

    def _on_sentence_begin(self, message, *args):
        pass

    def _on_sentence_end(self, message, *args):
        try:
            msg = self._parse_message(message)
            text = msg.get("payload", {}).get("result", "")
            if text:
                self._final_text = text
                if self._callback:
                    self._callback(text, True)
            logger.info(f"识别完成: {text}")
        except Exception as e:
            logger.error(f"处理最终结果出错: {e}")

    def _on_result_changed(self, message, *args):
        try:
            msg = self._parse_message(message)
            text = msg.get("payload", {}).get("result", "")
            if text and self._callback:
                self._final_text = text
                self._callback(text, False)
        except Exception as e:
            logger.error(f"处理中间结果出错: {e}")

    def _on_completed(self, message, *args):
        try:
            msg = self._parse_message(message)
            text = msg.get("payload", {}).get("result", "")
            if text:
                self._final_text = text
                if self._callback:
                    self._callback(text, True)
            logger.info(f"识别完成: {text}")
        except Exception as e:
            logger.error(f"处理最终结果出错: {e}")

    def _on_error(self, message, *args):
        msg = self._parse_message(message)
        logger.error(f"识别错误: {msg}")

    def _on_close(self, *args):
        self._is_ready = False
        logger.info("连接已关闭")

    def _on_final_chunk(self, silence_chunk=b'\x00\x00' * 16000):
        if self._sr:
            self._sr.send_audio(silence_chunk)

    # ---------- 发送线程（含保活机制） ----------
    def _send_audio_loop(self):
        """持续从队列取数据发送；无数据时发送静音包保持连接活跃"""
        last_send_time = time.time()
        silence_chunk = b'\x00\x00' * 320  # 640 字节静音

        while self._is_running and not self._stop_sending:
            try:
                chunk = self._audio_queue.get(timeout=0.2)
                if chunk == b"__END__":
                    self._on_final_chunk()
                    continue
                if chunk and self._sr:
                    for i in range(0, len(chunk), 640):
                        if self._stop_sending:
                            break
                        piece = chunk[i:i+640]
                        self._sr.send_audio(piece)
                        time.sleep(0.01)
                    last_send_time = time.time()
            except queue.Empty:
                # 队列空时检查是否需要发送静音保活（每 5 秒发一次）
                now = time.time()
                if now - last_send_time > 5 and self._is_running and self._sr:
                    self._sr.send_audio(silence_chunk)
                    last_send_time = now
                    time.sleep(0.01)
                continue
            except Exception as e:
                logger.error(f"发送音频出错: {e}")
                break