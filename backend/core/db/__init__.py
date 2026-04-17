from .base import DatabaseInterface
from .sqlite import SQLiteDatabase
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DatabaseFactory:
    _databases: Dict[str, type] = {
        "sqlite": SQLiteDatabase,
    }

    @classmethod
    def create_database(cls, db_type: str, **kwargs) -> Optional[DatabaseInterface]:
        if db_type not in cls._databases:
            logger.error(f"不支持的数据库类型: {db_type}")
            return None

        try:
            db_class = cls._databases[db_type]
            return db_class(**kwargs)
        except Exception as e:
            logger.error(f"创建数据库实例失败: {e}")
            return None

    @classmethod
    def register_database(cls, db_type: str, db_class: type):
        cls._databases[db_type] = db_class
        logger.info(f"注册数据库类型: {db_type}")

    @classmethod
    def get_supported_types(cls) -> list:
        return list(cls._databases.keys())


__all__ = [
    "DatabaseInterface",
    "SQLiteDatabase",
    "DatabaseFactory"
]