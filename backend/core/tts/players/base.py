from abc import ABC, abstractmethod

class BaseAudioPlayer(ABC):
    """音频播放器抽象基类"""

    @abstractmethod
    def play(self, audio_data: bytes, file_ext: str = ".mp3") -> None:
        """
        播放音频数据（字节流）
        :param audio_data: 音频二进制数据
        :param file_ext: 临时文件扩展名，默认 .mp3
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止当前播放"""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
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

    @abstractmethod
    def close(self) -> None:
        """释放资源"""
        pass