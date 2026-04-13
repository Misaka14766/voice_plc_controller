import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import pyads
from pyads.constants import PLCTYPE_INT, PLCTYPE_BOOL, PLCTYPE_REAL, PLCTYPE_STRING
from .base import BasePLC, MonitorGroup, TriggerMode
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
        self._groups: Dict[str, MonitorGroup] = {}
        self._group_last_values: Dict[str, Dict[str, Any]] = {}
        self._latest_values: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

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
        if not self.is_connected():
            return []
        try:
            symbols = self._conn.get_all_symbols()
            result = []
            for sym in symbols:
                type_name = str(sym.symbol_type) if hasattr(sym, 'symbol_type') else "UNKNOWN"
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

    def add_monitor_group(self, group: MonitorGroup) -> None:
        with self._lock:
            self._groups[group.group_id] = group
            self._group_last_values[group.group_id] = {}

    def remove_monitor_group(self, group_id: str) -> None:
        with self._lock:
            if group_id in self._groups:
                del self._groups[group_id]
            if group_id in self._group_last_values:
                del self._group_last_values[group_id]
            if group_id in self._latest_values:
                del self._latest_values[group_id]

    def start_monitoring(self):
        if self._monitoring:
            return
        if not self.is_connected():
            raise RuntimeError("PLC not connected")
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self._monitor_thread = None

    def _monitor_loop(self):
        # 为每个组记录上次轮询时间，按需休眠
        while self._monitoring and self.is_connected():
            with self._lock:
                groups = list(self._groups.values())
            for group in groups:
                # 读取该组所有变量
                values = {}
                for var_name, var_type in group.variables:
                    try:
                        ads_type = self._type_map.get(var_type.upper(), PLCTYPE_INT)
                        val = self._conn.read_by_name(var_name, ads_type)
                        values[var_name] = val
                    except Exception as e:
                        values[var_name] = f"Error: {e}"
                with self._lock:
                    self._latest_values[group.group_id] = values
                    last_vals = self._group_last_values.get(group.group_id, {})
                    should_call = False
                    if group.mode == TriggerMode.ALWAYS:
                        should_call = True
                    elif group.mode == TriggerMode.ON_CHANGE:
                        if values != last_vals:
                            should_call = True
                    if should_call:
                        try:
                            group.callback(values)
                        except Exception as e:
                            print(f"监控回调异常: {e}")
                    self._group_last_values[group.group_id] = values.copy()
            # 简单休眠（可优化为动态最小间隔）
            time.sleep(0.05)

    def get_monitored_values(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if group_id:
                return self._latest_values.get(group_id, {}).copy()
            # 返回所有组的最新值合并
            all_vals = {}
            for gid, vals in self._latest_values.items():
                all_vals.update(vals)
            return all_vals

    # 保留原有异步生成器方法（可选）
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