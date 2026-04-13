import edge_tts
import logging
from .base import BaseTTS
from backend.config import settings
from .players.factory import get_player

logger = logging.getLogger(__name__)


class EdgeTTS(BaseTTS):
    def __init__(self):
        self.voice = settings.TTS_VOICE
        self.player = get_player()
        self._volume = settings.TTS_VOLUME
        self.player.set_volume(self._volume)
        logger.info(f"Edge TTS 初始化完成，播放器: {settings.TTS_PLAYER}")

    async def speak(self, text: str):
        """合成并立即播放（无返回值）"""
        audio_data = await self.synthesize_async(text)
        if audio_data:
            self.player.play(audio_data, ".mp3")

    async def synthesize_async(self, text: str) -> bytes:
        """异步合成语音，返回音频字节数据"""
        if not text:
            return b""
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)

    def stop(self):
        self.player.stop()

    def set_volume(self, volume: float):
        self._volume = volume
        self.player.set_volume(volume)

    def get_volume(self) -> float:
        return self.player.get_volume()

    def is_playing(self) -> bool:
        return self.player.is_playing()

    def close(self):
        self.player.close()