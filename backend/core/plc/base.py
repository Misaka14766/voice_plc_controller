from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

class TriggerMode(Enum):
    ON_CHANGE = "on_change"      # 仅当值变化时触发回调
    ALWAYS = "always"            # 每次轮询都触发回调

@dataclass
class MonitorGroup:
    variables: List[Tuple[str, str]]  # [(var_name, type), ...]
    callback: Callable[[Dict[str, Any]], None]
    mode: TriggerMode = TriggerMode.ALWAYS
    interval_ms: int = 100
    group_id: str = ""

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
        pass

    @abstractmethod
    def add_monitor_group(self, group: MonitorGroup) -> None:
        """添加一个监控组"""
        pass

    @abstractmethod
    def remove_monitor_group(self, group_id: str) -> None:
        """移除监控组"""
        pass

    @abstractmethod
    def start_monitoring(self):
        """启动所有监控组的后台线程（如果尚未启动）"""
        pass

    @abstractmethod
    def stop_monitoring(self):
        """停止所有监控"""
        pass

    @abstractmethod
    def get_monitored_values(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        """获取最新监控值"""
        pass