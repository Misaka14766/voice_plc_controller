import edge_tts
import tempfile
import os
import subprocess
import platform
from .base import BaseTTS
from backend.config import settings

class EdgeTTS(BaseTTS):
    async def speak(self, text: str):
        if not text:
            return
        communicate = edge_tts.Communicate(text, settings.TTS_VOICE)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            await communicate.save(f.name)
            self._play(f.name)
            os.unlink(f.name)

    async def synthesize_async(self, text: str) -> bytes:
        """异步合成语音，返回音频字节数据"""
        if not text:
            return b""
        communicate = edge_tts.Communicate(text, settings.TTS_VOICE)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)

    def _play(self, path):
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["afplay", path])
        else:
            subprocess.run(["mpg123", "-q", path])