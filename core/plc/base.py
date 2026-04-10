from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

class BasePLC(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def read(self, var_name: str, plc_type: str = "INT") -> Any:
        pass

    @abstractmethod
    def write(self, var_name: str, value: Any, plc_type: str = "INT") -> bool:
        pass

    @abstractmethod
    def read_bool(self, var_name: str) -> bool:
        pass

    @abstractmethod
    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """
        获取 PLC 中所有可访问的变量符号信息。
        返回格式示例：
        [
            {"name": "MAIN.TestInt", "type": "INT", "comment": ""},
            {"name": "MAIN.TestBool", "type": "BOOL", "comment": ""},
            ...
        ]
        """
        pass

    # 监控相关方法保持不变
    @abstractmethod
    def start_monitoring(self, variables: List[Tuple[str, str]],
                         callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                         interval_ms: int = 100):
        pass

    @abstractmethod
    def stop_monitoring(self):
        pass

    @abstractmethod
    def get_monitored_values(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def async_monitor_generator(self, variables: List[Tuple[str, str]], interval_ms: int = 100):
        pass