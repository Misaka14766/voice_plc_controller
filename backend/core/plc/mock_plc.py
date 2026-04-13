import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from .base import BasePLC, MonitorGroup, TriggerMode

class MockPLC(BasePLC):
    def __init__(self):
        self._state = {
            "MAIN.bVoiceTrigger": False,
            "MAIN.TestInt": 0,
            "MAIN.TestBool": False,
            "MAIN.TestReal": 0.0,
            "MAIN.WaterLevel": 50.0,
            "MAIN.Temperature": 25.5,
            "MAIN.MotorRun": False,
            "MAIN.Pressure": 101.3,
        }
        self._connected = False
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._groups: Dict[str, MonitorGroup] = {}
        self._group_last_values: Dict[str, Dict[str, Any]] = {}
        self._latest_values: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # ========== 自动反转语音触发器 ==========
        self._toggle_trigger = True
        self._toggle_thread = threading.Thread(target=self._toggle_voice_trigger, daemon=True)
        self._toggle_thread.start()

    def _toggle_voice_trigger(self):
        """每隔 3 秒反转一次 MAIN.bVoiceTrigger 的值"""
        while self._toggle_trigger:
            time.sleep(3)
            with self._lock:
                current = self._state.get("MAIN.bVoiceTrigger", False)
                self._state["MAIN.bVoiceTrigger"] = not current
                print(f"[MockPLC] bVoiceTrigger 自动反转 -> {self._state['MAIN.bVoiceTrigger']}")

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self.stop_monitoring()
        self._toggle_trigger = False
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read(self, var_name: str, plc_type: str = "INT"):
        return self._state.get(var_name)

    def write(self, var_name: str, value, plc_type: str = "INT") -> bool:
        if var_name in self._state:
            self._state[var_name] = value
            return True
        return False

    def read_bool(self, var_name: str) -> bool:
        val = self._state.get(var_name, False)
        return bool(val)

    def get_all_symbols(self) -> List[Dict[str, Any]]:
        symbols = []
        for name, value in self._state.items():
            if isinstance(value, bool):
                var_type = "BOOL"
            elif isinstance(value, int):
                var_type = "INT"
            elif isinstance(value, float):
                var_type = "REAL"
            else:
                var_type = "STRING"
            symbols.append({
                "name": name,
                "type": var_type,
                "comment": "模拟变量"
            })
        return symbols

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
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self._monitor_thread = None

    def _monitor_loop(self):
        while self._monitoring:
            with self._lock:
                groups = list(self._groups.values())
            for group in groups:
                values = {}
                for var_name, _ in group.variables:
                    values[var_name] = self._state.get(var_name)
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
            time.sleep(0.05)

    def get_monitored_values(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if group_id:
                return self._latest_values.get(group_id, {}).copy()
            all_vals = {}
            for gid, vals in self._latest_values.items():
                all_vals.update(vals)
            return all_vals

    async def async_monitor_generator(self, variables: List[Tuple[str, str]], interval_ms: int = 100):
        interval = interval_ms / 1000.0
        while True:
            values = {}
            for var_name, _ in variables:
                values[var_name] = self._state.get(var_name)
            yield values
            await asyncio.sleep(interval)