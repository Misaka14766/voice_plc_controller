from abc import ABC, abstractmethod
from typing import Optional, Callable

class BaseASR(ABC):
    @abstractmethod
    def feed_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        """喂入音频块，返回当前识别文本（流式中间结果）"""
        pass

    @abstractmethod
    def reset(self):
        """重置状态"""
        pass

    @abstractmethod
    def start(self):
        """启动识别会话（对于需要建立连接的远程ASR）"""
        pass

    @abstractmethod
    def stop(self):
        """停止识别会话，关闭连接"""
        pass

    @abstractmethod
    def set_callback(self, callback: Optional[Callable[[str, bool], None]] = None):
        """设置识别结果回调函数，参数为 (text, is_final)"""
        pass