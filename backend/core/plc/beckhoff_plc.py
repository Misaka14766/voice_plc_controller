import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import pyads
from pyads.constants import PLCTYPE_INT, PLCTYPE_BOOL, PLCTYPE_REAL, PLCTYPE_STRING
from .base import BasePLC
from backend.config import settings

class BeckhoffPLC(BasePLC):
    def __init__(self):
        self._conn: Optional[pyads.Connection] = None
        self._type_map = {
            "BOOL": PLCTYPE_BOOL,
            "INT": PLCTYPE_INT,
            "REAL": PLCTYPE_REAL,
            "STRING": PLCTYPE_STRING,
        }
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_variables: List[Tuple[str, int]] = []
        self._monitor_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._monitor_interval = 0.1
        self._latest_values: Dict[str, Any] = {}

    def connect(self) -> bool:
        try:
            self._conn = pyads.Connection(
                ams_net_id=settings.PLC_AMS_NET_ID,
                ams_net_port=settings.PLC_AMS_PORT,
                ip_address=settings.PLC_IP_ADDRESS
            )
            self._conn.open()
            _ = self._conn.read_device_info()
            return True
        except Exception as e:
            print(f"PLC 连接失败: {e}")
            return False

    def disconnect(self):
        self.stop_monitoring()
        if self._conn and self._conn.is_open:
            self._conn.close()
        self._conn = None

    def is_connected(self) -> bool:
        return self._conn is not None and self._conn.is_open

    def read(self, var_name: str, plc_type: str = "INT") -> Any:
        if not self.is_connected():
            raise RuntimeError("PLC not connected")
        ads_type = self._type_map.get(plc_type.upper(), PLCTYPE_INT)
        return self._conn.read_by_name(var_name, ads_type)

    def write(self, var_name: str, value: Any, plc_type: str = "INT") -> bool:
        if not self.is_connected():
            return False
        try:
            ads_type = self._type_map.get(plc_type.upper(), PLCTYPE_INT)
            if ads_type == PLCTYPE_BOOL:
                value = bool(value)
            elif ads_type == PLCTYPE_INT:
                value = int(value)
            elif ads_type == PLCTYPE_REAL:
                value = float(value)
            self._conn.write_by_name(var_name, value, ads_type)
            return True
        except Exception:
            return False

    def read_bool(self, var_name: str) -> bool:
        if not self.is_connected():
            return False
        try:
            return self._conn.read_by_name(var_name, PLCTYPE_BOOL)
        except Exception:
            return False

    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """获取 PLC 中所有变量符号信息"""
        if not self.is_connected():
            return []
        try:
            symbols = self._conn.get_all_symbols()
            result = []
            for sym in symbols:
                # 获取类型名称
                type_name = str(sym.symbol_type) if hasattr(sym, 'symbol_type') else "UNKNOWN"
                # 尝试提取注释（如果可用）
                comment = sym.comment if hasattr(sym, 'comment') else ""
                result.append({
                    "name": sym.name,
                    "type": type_name,
                    "comment": comment
                })
            return result
        except Exception as e:
            print(f"获取符号列表失败: {e}")
            return []

    # 监控方法实现（与之前相同，此处省略以节省篇幅）
    def start_monitoring(self, variables: List[Tuple[str, str]],
                         callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                         interval_ms: int = 100):
        if not self.is_connected():
            raise RuntimeError("PLC not connected")
        if self._monitoring:
            self.stop_monitoring()
        self._monitor_variables = []
        for var_name, var_type in variables:
            ads_type = self._type_map.get(var_type.upper(), PLCTYPE_INT)
            self._monitor_variables.append((var_name, ads_type))
        self._monitor_callback = callback
        self._monitor_interval = interval_ms / 1000.0
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self):
        while self._monitoring and self.is_connected():
            values = {}
            for var_name, ads_type in self._monitor_variables:
                try:
                    val = self._conn.read_by_name(var_name, ads_type)
                    values[var_name] = val
                except Exception as e:
                    values[var_name] = f"Error: {e}"
            self._latest_values = values
            if self._monitor_callback:
                try:
                    self._monitor_callback(values)
                except Exception as e:
                    print(f"监控回调异常: {e}")
            time.sleep(self._monitor_interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None

    def get_monitored_values(self) -> Dict[str, Any]:
        return self._latest_values.copy()

    async def async_monitor_generator(self, variables: List[Tuple[str, str]], interval_ms: int = 100):
        if not self.is_connected():
            raise RuntimeError("PLC not connected")
        ads_vars = []
        for var_name, var_type in variables:
            ads_type = self._type_map.get(var_type.upper(), PLCTYPE_INT)
            ads_vars.append((var_name, ads_type))
        interval = interval_ms / 1000.0
        while True:
            values = {}
            for var_name, ads_type in ads_vars:
                try:
                    val = self._conn.read_by_name(var_name, ads_type)
                    values[var_name] = val
                except Exception as e:
                    values[var_name] = f"Error: {e}"
            yield values
            await asyncio.sleep(interval)