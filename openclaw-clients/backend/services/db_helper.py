"""
数据库工具类
统一管理 SQLite 数据库连接，减少重复代码
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """
    SQLite 数据库工具类
    
    使用示例:
        db = DatabaseHelper('mydb.db')
        
        # 使用上下文管理器自动关闭连接
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            
        # 或者使用便捷方法
        users = db.fetch_all("SELECT * FROM users")
        user = db.fetch_one("SELECT * FROM users WHERE id = ?", (1,))
        db.execute("INSERT INTO users (name) VALUES (?)", ("张三",))
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @contextmanager
    def connection(self):
        """
        获取数据库连接（上下文管理器）
        自动关闭连接
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            logger.error(f"数据库错误: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """
        执行 SQL 语句（INSERT, UPDATE, DELETE）
        
        Returns:
            lastrowid 或 affected rows
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid or cursor.rowcount
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行 SQL 语句
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount
    
    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        
        Returns:
            字典格式的记录，或 None
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        查询多条记录
        
        Returns:
            字典列表
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def fetch_value(self, sql: str, params: tuple = ()) -> Any:
        """
        查询单个值
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入记录
        
        Args:
            table: 表名
            data: 字段字典
            
        Returns:
            新记录的 ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        """
        更新记录
        
        Args:
            table: 表名
            data: 要更新的字段字典
            where: WHERE 条件
            where_params: WHERE 参数
            
        Returns:
            影响的行数
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params
        return self.execute(sql, params)
    
    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        """
        删除记录
        
        Returns:
            影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.execute(sql, where_params)
    
    def count(self, table: str, where: str = None, where_params: tuple = ()) -> int:
        """
        统计记录数
        """
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.fetch_value(sql, where_params) or 0
    
    def table_exists(self, table: str) -> bool:
        """
        检查表是否存在
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        return self.fetch_value(sql, (table,)) is not None
    
    def create_table(self, table: str, columns: str, if_not_exists: bool = True):
        """
        创建表
        
        Args:
            table: 表名
            columns: 列定义（如 "id INTEGER PRIMARY KEY, name TEXT"）
            if_not_exists: 是否添加 IF NOT EXISTS
        """
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        sql = f"CREATE TABLE {exists_clause}{table} ({columns})"
        self.execute(sql)