import tempfile
import os
import subprocess
import platform
import threading
import time
import logging
from .base import BaseAudioPlayer

logger = logging.getLogger(__name__)


class SystemPlayer(BaseAudioPlayer):
    """使用系统默认播放器的降级方案"""

    def __init__(self):
        self._volume = 0.8  # 音量控制可能无效（仅作占位）
        self._process = None
        self._stop_flag = threading.Event()

    def play(self, audio_data: bytes, file_ext: str = ".mp3"):
        if not audio_data:
            return
        self.stop()

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        def _play_and_cleanup():
            system = platform.system()
            try:
                if system == "Windows":
                    self._process = subprocess.Popen(["start", "/wait", temp_path], shell=True)
                elif system == "Darwin":
                    self._process = subprocess.Popen(["afplay", temp_path])
                else:
                    self._process = subprocess.Popen(["mpg123", "-q", temp_path])
                # 等待进程结束或收到停止信号
                while self._process.poll() is None and not self._stop_flag.is_set():
                    time.sleep(0.1)
                if self._stop_flag.is_set() and self._process.poll() is None:
                    self._process.terminate()
            except Exception as e:
                logger.error(f"系统播放器出错: {e}")
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception:
                    pass

        self._stop_flag.clear()
        threading.Thread(target=_play_and_cleanup, daemon=True).start()

    def stop(self):
        self._stop_flag.set()
        if self._process and self._process.poll() is None:
            self._process.terminate()

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        # 系统播放器通常不支持音量控制，此处仅记录
        logger.debug(f"音量设置为 {self._volume}（系统播放器可能不支持）")

    def get_volume(self) -> float:
        return self._volume

    def is_playing(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def close(self):
        self.stop()