import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from .base import DatabaseInterface

logger = logging.getLogger(__name__)


class SQLiteDatabase(DatabaseInterface):
    def __init__(self, db_path: str = "plc_data.db"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._connected = False

    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            self._connected = True
            logger.info(f"SQLite 数据库连接成功: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite 数据库连接失败: {e}")
            return False

    def disconnect(self) -> bool:
        try:
            if self.connection:
                self.connection.close()
                self._connected = False
                logger.info("SQLite 数据库连接已关闭")
                return True
        except Exception as e:
            logger.error(f"关闭 SQLite 数据库连接失败: {e}")
            return False

    def _create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plc_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variable_name TEXT NOT NULL,
                value REAL,
                data_type TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_variable_name ON plc_data(variable_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON plc_data(timestamp)
        """)
        
        self.connection.commit()

    def save_plc_data(self, variable_name: str, value: Any, data_type: str) -> bool:
        try:
            cursor = self.connection.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO plc_data (variable_name, value, data_type, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (variable_name, float(value) if value is not None else 0.0, data_type, timestamp)
            )
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"保存 PLC 数据失败: {variable_name} = {value}, 错误: {e}")
            return False

    def save_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        try:
            cursor = self.connection.cursor()
            timestamp = datetime.now().isoformat()
            
            records = []
            for data in data_list:
                records.append((
                    data.get("variable_name"),
                    float(data.get("value", 0.0)) if data.get("value") is not None else 0.0,
                    data.get("data_type", "REAL"),
                    timestamp
                ))
            
            cursor.executemany(
                """
                INSERT INTO plc_data (variable_name, value, data_type, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                records
            )
            self.connection.commit()
            logger.debug(f"批量保存成功: {len(records)} 条数据")
            return True
        except Exception as e:
            logger.error(f"批量保存失败: {e}")
            return False

    def get_latest_values(self, variable_names: List[str]) -> Dict[str, Any]:
        try:
            cursor = self.connection.cursor()
            placeholders = ",".join(["?"] * len(variable_names))
            
            query = f"""
                SELECT variable_name, value, data_type, timestamp
                FROM plc_data
                WHERE variable_name IN ({placeholders})
                AND id IN (
                    SELECT MAX(id) FROM plc_data
                    WHERE variable_name IN ({placeholders})
                    GROUP BY variable_name
                )
            """
            
            cursor.execute(query, variable_names + variable_names)
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                result[row["variable_name"]] = {
                    "value": row["value"],
                    "data_type": row["data_type"],
                    "timestamp": row["timestamp"]
                }
            
            return result
        except Exception as e:
            logger.error(f"获取最新值失败: {e}")
            return {}

    def query_history(
        self,
        variable_name: str,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT variable_name, value, data_type, timestamp
                FROM plc_data
                WHERE variable_name = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                """,
                (variable_name, start_time, end_time)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "variable_name": row["variable_name"],
                    "value": row["value"],
                    "data_type": row["data_type"],
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"查询历史数据失败: {e}")
            return []

    def query_aggregated(
        self,
        variable_name: str,
        start_time: str,
        end_time: str,
        window_seconds: int,
        aggregation: str
    ) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            
            agg_func = {
                "mean": "AVG",
                "max": "MAX",
                "min": "MIN",
                "sum": "SUM",
                "first": "MIN",
                "last": "MAX"
            }.get(aggregation, "AVG")
            
            if aggregation == "first":
                cursor.execute(
                    f"""
                    SELECT 
                        variable_name,
                        {agg_func}(value) as value,
                        MIN(timestamp) as timestamp
                    FROM plc_data
                    WHERE variable_name = ? AND timestamp >= ? AND timestamp <= ?
                    GROUP BY CAST(strftime('%s', timestamp) / ? AS INTEGER)
                    ORDER BY timestamp ASC
                    """,
                    (variable_name, start_time, end_time, window_seconds)
                )
            elif aggregation == "last":
                cursor.execute(
                    f"""
                    SELECT 
                        variable_name,
                        {agg_func}(value) as value,
                        MAX(timestamp) as timestamp
                    FROM plc_data
                    WHERE variable_name = ? AND timestamp >= ? AND timestamp <= ?
                    GROUP BY CAST(strftime('%s', timestamp) / ? AS INTEGER)
                    ORDER BY timestamp ASC
                    """,
                    (variable_name, start_time, end_time, window_seconds)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT 
                        variable_name,
                        {agg_func}(value) as value,
                        MIN(timestamp) as timestamp
                    FROM plc_data
                    WHERE variable_name = ? AND timestamp >= ? AND timestamp <= ?
                    GROUP BY CAST(strftime('%s', timestamp) / ? AS INTEGER)
                    ORDER BY timestamp ASC
                    """,
                    (variable_name, start_time, end_time, window_seconds)
                )
            
            rows = cursor.fetchall()
            
            return [
                {
                    "variable_name": row["variable_name"],
                    "value": row["value"],
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"查询聚合数据失败: {e}")
            return []

    def is_connected(self) -> bool:
        return self._connected and self.connection is not None

    def get_status(self) -> Dict[str, Any]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM plc_data")
            total_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(DISTINCT variable_name) as count FROM plc_data")
            variable_count = cursor.fetchone()["count"]
            
            return {
                "connected": self._connected,
                "db_path": self.db_path,
                "total_records": total_count,
                "variable_count": variable_count
            }
        except Exception as e:
            logger.error(f"获取数据库状态失败: {e}")
            return {
                "connected": self._connected,
                "db_path": self.db_path,
                "error": str(e)
            }

    def clear_variable_data(self, variable_name: str) -> bool:
        """清空指定变量的数据"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM plc_data WHERE variable_name = ?", (variable_name,))
            affected_rows = cursor.rowcount
            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='plc_data'")
            self.connection.commit()
            logger.info(f"已清空变量 {variable_name} 的数据，影响 {affected_rows} 条记录，自增ID已重置")
            return True
        except Exception as e:
            logger.error(f"清空变量数据失败: {e}")
            return False

    def clear_all_data(self) -> bool:
        """清空所有数据"""
        try:
            cursor = self.connection.cursor()
            # 清空数据
            cursor.execute("DELETE FROM plc_data")
            affected_rows = cursor.rowcount
            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='plc_data'")
            self.connection.commit()
            logger.info(f"已清空所有数据，影响 {affected_rows} 条记录，自增ID已重置")
            return True
        except Exception as e:
            logger.error(f"清空所有数据失败: {e}")
            return False
    
    def get_all_variables(self) -> List[str]:
        """获取所有变量名"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT variable_name FROM plc_data")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"获取所有变量失败: {e}")
            return []