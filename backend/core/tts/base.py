from abc import ABC, abstractmethod

class BaseTTS(ABC):
    @abstractmethod
    async def speak(self, text: str):
        """异步语音合成并播放"""
        pass

    @abstractmethod
    async def synthesize_async(self, text: str) -> bytes:
        """异步合成语音，返回音频数据"""
        pass

    @abstractmethod
    def stop(self):
        """停止当前播放"""
        pass

    @abstractmethod
    def set_volume(self, volume: float):
        """设置音量 (0.0 ~ 1.0)"""
        pass

    @abstractmethod
    def get_volume(self) -> float:
        """获取当前音量"""
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        """是否正在播放"""
        pass