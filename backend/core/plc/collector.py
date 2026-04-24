import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class VariableInfo:
    def __init__(self, name: str, data_type: str = "REAL"):
        self.name = name
        self.data_type = data_type


class PLCCollector:
    def __init__(
        self,
        plc,
        db_manager=None,
        interval_ms: int = 1000
    ):
        self.plc = plc
        self.db_manager = db_manager
        self.interval_ms = interval_ms
        self.variables: List[VariableInfo] = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
        self._on_collect_callback: Optional[Callable] = None
        self._batch_buffer: List[Dict[str, Any]] = []
        self._batch_size = 10
        self._last_save_time = datetime.now()

    def add_variable(self, name: str, data_type: str = "REAL"):
        self.variables.append(VariableInfo(name, data_type))
        logger.info(f"添加采集变量: {name} ({data_type})")

    def set_interval(self, interval_ms: int):
        self.interval_ms = interval_ms
        logger.info(f"采集间隔设置为: {interval_ms}ms")

    def set_batch_size(self, batch_size: int):
        self._batch_size = batch_size
        logger.info(f"批处理大小设置为: {batch_size}")

    def set_on_collect_callback(self, callback: Callable):
        self._on_collect_callback = callback

    def set_db_manager(self, db_manager):
        self.db_manager = db_manager

    def collect_once(self) -> List[Dict[str, Any]]:
        if not self.plc or not self.plc.is_connected():
            logger.warning("PLC未连接，无法采集数据")
            return []

        collected_data = []
        for var in self.variables:
            try:
                value = self.plc.read(var.name, var.data_type)
                data = {
                    "variable_name": var.name,
                    "value": value,
                    "data_type": var.data_type,
                    "timestamp": datetime.now().isoformat()
                }
                collected_data.append(data)

                if self.db_manager:
                    self.db_manager.save_plc_data(var.name, value, var.data_type)

                if self._on_collect_callback:
                    self._on_collect_callback(var.name, value, var.data_type)

            except Exception as e:
                logger.error(f"采集变量失败: {var.name}, 错误: {e}")

        return collected_data

    def collect_batch(self) -> bool:
        collected = self.collect_once()
        if not collected:
            return False

        self._batch_buffer.extend(collected)

        if len(self._batch_buffer) >= self._batch_size:
            return self._flush_batch()

        return True

    def _flush_batch(self) -> bool:
        if not self._batch_buffer or not self.db_manager:
            return False

        success = self.db_manager.save_batch(self._batch_buffer)
        if success:
            logger.debug(f"批量保存成功: {len(self._batch_buffer)} 条数据")
            self._batch_buffer.clear()
            self._last_save_time = datetime.now()
        else:
            logger.error(f"批量保存失败")

        return success

    async def _collect_task_async(self):
        while self.running:
            try:
                self.collect_batch()
            except Exception as e:
                logger.error(f"异步采集任务错误: {e}")

            await asyncio.sleep(self.interval_ms / 1000)

    def start_async(self):
        if self.running:
            logger.warning("采集器已在运行")
            return

        self.running = True
        self._task = asyncio.create_task(self._collect_task_async())
        logger.info(f"异步采集任务已启动，间隔: {self.interval_ms}ms")

    async def stop_async(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._flush_batch()
        logger.info("异步采集任务已停止")

    def _collect_thread_target(self):
        while self.running:
            try:
                self.collect_once()
            except Exception as e:
                logger.error(f"线程采集任务错误: {e}")

            threading.Event().wait(self.interval_ms / 1000)

    def start_thread(self):
        if self.running:
            logger.warning("采集器已在运行")
            return

        self.running = True
        self._thread = threading.Thread(target=self._collect_thread_target, daemon=True)
        self._thread.start()
        logger.info(f"线程采集任务已启动，间隔: {self.interval_ms}ms")

    def stop_thread(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._flush_batch()
        logger.info("线程采集任务已停止")

    def start(self):
        self.start_async()

    def stop(self):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.stop_async())
        else:
            loop.run_until_complete(self.stop_async())

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "interval_ms": self.interval_ms,
            "variables_count": len(self.variables),
            "variables": [v.name for v in self.variables],
            "buffer_size": len(self._batch_buffer),
            "batch_size": self._batch_size,
            "plc_connected": self.plc.is_connected() if self.plc else False,
            "db_available": self.db_manager is not None
        }