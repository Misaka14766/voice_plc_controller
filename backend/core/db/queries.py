import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryBuilder:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_realtime_all(self, variable_names: List[str]) -> Dict[str, Any]:
        return self.db.get_latest_values(variable_names)

    def get_history_range(
        self,
        variable_name: str,
        hours: int = 1,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        if end_time is None:
            end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        return self.db.query_history(
            variable_name,
            start_time.isoformat(),
            end_time.isoformat()
        )

    def get_aggregated_data(
        self,
        variable_name: str,
        hours: int = 1,
        window_seconds: int = 60,
        aggregation: str = "mean",
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        if end_time is None:
            end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        return self.db.query_aggregated(
            variable_name,
            start_time.isoformat(),
            end_time.isoformat(),
            window_seconds,
            aggregation
        )

    def get_multiple_variables_history(
        self,
        variable_names: List[str],
        hours: int = 1,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        if end_time is None:
            end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        return self.db.query_multiple_variables(
            variable_names,
            start_time.isoformat(),
            end_time.isoformat()
        )


class DataQuerier:
    _instance: Optional['QueryBuilder'] = None

    @classmethod
    def get_instance(cls) -> Optional['QueryBuilder']:
        return cls._instance

    @classmethod
    def init_instance(cls, db_manager):
        if cls._instance is None:
            cls._instance = QueryBuilder(db_manager)
        return cls._instance

    @classmethod
    def get_realtime(cls, variable_names: List[str]) -> Dict[str, Any]:
        if cls._instance:
            return cls._instance.get_realtime_all(variable_names)
        return {}

    @classmethod
    def get_history(
        cls,
        variable_name: str,
        hours: int = 1,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        if cls._instance:
            return cls._instance.get_history_range(variable_name, hours, end_time)
        return []

    @classmethod
    def get_aggregated(
        cls,
        variable_name: str,
        hours: int = 1,
        window_seconds: int = 60,
        aggregation: str = "mean",
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        if cls._instance:
            return cls._instance.get_aggregated_data(
                variable_name, hours, window_seconds, aggregation, end_time
            )
        return []

    @classmethod
    def get_chart_data(
        cls,
        variable_name: str,
        time_range: str = "1h",
        aggregation: str = "mean"
    ) -> Dict[str, Any]:
        hours_map = {
            "30m": 0.5,
            "1h": 1,
            "6h": 6,
            "12h": 12,
            "24h": 24,
            "7d": 168
        }
        hours = hours_map.get(time_range, 1)

        window_seconds = int(hours * 60 * 60 / 100)
        if window_seconds < 60:
            window_seconds = 60

        data = cls.get_aggregated(
            variable_name,
            hours=hours,
            window_seconds=window_seconds,
            aggregation=aggregation
        )

        return {
            "variable": variable_name,
            "time_range": time_range,
            "aggregation": aggregation,
            "data_points": len(data),
            "data": data
        }
