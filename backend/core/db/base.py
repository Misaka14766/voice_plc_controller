from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    @abstractmethod
    def save_plc_data(self, variable_name: str, value: Any, data_type: str) -> bool:
        pass

    @abstractmethod
    def save_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    def get_latest_values(self, variable_names: List[str]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def query_history(
        self,
        variable_name: str,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def query_aggregated(
        self,
        variable_name: str,
        start_time: str,
        end_time: str,
        window_seconds: int,
        aggregation: str
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def clear_variable_data(self, variable_name: str) -> bool:
        """清空指定变量的数据"""
        pass

    @abstractmethod
    def clear_all_data(self) -> bool:
        """清空所有数据"""
        pass
    
    @abstractmethod
    def get_all_variables(self) -> List[str]:
        """获取所有变量名"""
        pass