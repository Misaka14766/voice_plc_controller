import edge_tts
import tempfile
import os
import subprocess
import platform
from .base import BaseTTS
from config.settings import settings

class EdgeTTS(BaseTTS):
    async def speak(self, text: str):
        if not text:
            return
        communicate = edge_tts.Communicate(text, settings.TTS_VOICE)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            await communicate.save(f.name)
            self._play(f.name)
            os.unlink(f.name)

    def _play(self, path):
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["afplay", path])
        else:
            subprocess.run(["mpg123", "-q", path])