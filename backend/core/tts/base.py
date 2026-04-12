from abc import ABC, abstractmethod

class BaseTTS(ABC):
    @abstractmethod
    async def speak(self, text: str):
        """异步语音合成并播放"""
        pass