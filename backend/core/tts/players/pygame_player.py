import tempfile
import os
import threading
import time
import logging
import pygame
from .base import BaseAudioPlayer

logger = logging.getLogger(__name__)


class PygamePlayer(BaseAudioPlayer):
    """基于 Pygame 的跨平台音频播放器"""

    def __init__(self):
        self._volume = 0.8
        self._initialized = False
        self._current_sound = None
        self._play_thread = None
        self._stop_flag = threading.Event()
        self._init_pygame()

    def _init_pygame(self):
        try:
            pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=512)
            pygame.mixer.music.set_volume(self._volume)
            self._initialized = True
            logger.info("Pygame 音频播放器初始化成功")
        except Exception as e:
            logger.error(f"Pygame 初始化失败: {e}，请检查音频驱动")
            self._initialized = False

    def play(self, audio_data: bytes, file_ext: str = ".mp3"):
        if not audio_data:
            return
        if not self._initialized:
            logger.warning("Pygame 未就绪，播放失败")
            return

        # 先停止当前播放
        self.stop()

        # 写入临时文件（Pygame 需从文件加载）
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        def _play_and_cleanup():
            try:
                self._current_sound = pygame.mixer.Sound(temp_path)
                self._current_sound.set_volume(self._volume)
                self._current_sound.play()
                # 等待播放完成或被停止
                while pygame.mixer.get_busy() and not self._stop_flag.is_set():
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"播放出错: {e}")
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception:
                    pass
                self._current_sound = None

        self._stop_flag.clear()
        self._play_thread = threading.Thread(target=_play_and_cleanup, daemon=True)
        self._play_thread.start()

    def stop(self):
        self._stop_flag.set()
        if self._initialized:
            if self._current_sound:
                self._current_sound.stop()
            pygame.mixer.stop()
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=1.0)

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        if self._initialized:
            if self._current_sound:
                self._current_sound.set_volume(self._volume)
            pygame.mixer.music.set_volume(self._volume)

    def get_volume(self) -> float:
        return self._volume

    def is_playing(self) -> bool:
        if self._initialized:
            return pygame.mixer.get_busy()
        return False

    def close(self):
        self.stop()
        if self._initialized:
            pygame.mixer.quit()
            self._initialized = False