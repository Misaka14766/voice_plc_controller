import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from .base import BasePLC


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
        self._monitor_variables: List[Tuple[str, str]] = []
        self._monitor_callback = None
        self._monitor_interval = 0.1
        self._latest_values = {}

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self.stop_monitoring()
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
        """返回模拟变量列表"""
        symbols = []
        for name, value in self._state.items():
            # 根据值推断类型
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

    # 监控方法同 beckhoff_plc.py，此处省略
    def start_monitoring(self, variables: List[Tuple[str, str]],
                         callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                         interval_ms: int = 100):
        self._monitor_variables = variables
        self._monitor_callback = callback
        self._monitor_interval = interval_ms / 1000.0
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self):
        while self._monitoring:
            values = {}
            for var_name, _ in self._monitor_variables:
                values[var_name] = self._state.get(var_name)
            self._latest_values = values
            if self._monitor_callback:
                self._monitor_callback(values)
            time.sleep(self._monitor_interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None

    def get_monitored_values(self) -> Dict[str, Any]:
        return self._latest_values.copy()

    async def async_monitor_generator(self, variables: List[Tuple[str, str]], interval_ms: int = 100):
        interval = interval_ms / 1000.0
        while True:
            values = {}
            for var_name, _ in variables:
                values[var_name] = self._state.get(var_name)
            yield values
            await asyncio.sleep(interval)