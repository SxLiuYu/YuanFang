import logging
logger = logging.getLogger(__name__)
"""
家庭设备数据服务
读取设备数据、历史记录、统计分析
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class DeviceDataService:
    """家庭设备数据服务"""
    
    def __init__(self, db_path: str = "family_devices.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 设备表
        c.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE,
                device_name TEXT,
                device_type TEXT,
                platform TEXT,
                room TEXT,
                is_online BOOLEAN,
                created_at TIMESTAMP
            )
        ''')
        
        # 设备状态历史表
        c.execute('''
            CREATE TABLE IF NOT EXISTS device_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                status TEXT,
                value TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        
        # 能耗记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS energy_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                power_consumption REAL,
                recorded_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_device(self, device_id: str, device_name: str, device_type: str, 
                   platform: str, room: str) -> bool:
        """添加设备"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO devices (device_id, device_name, device_type, platform, room, is_online, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (device_id, device_name, device_type, platform, room, True, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"添加设备失败：{e}")
            return False
    
    def update_device_status(self, device_id: str, status: str, value: str = None):
        """更新设备状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 更新设备在线状态
            c.execute('''
                UPDATE devices SET is_online = ? WHERE device_id = ?
            ''', (1 if status == 'online' else 0, device_id))
            
            # 记录状态历史
            c.execute('''
                INSERT INTO device_status_history (device_id, status, value, recorded_at)
                VALUES (?, ?, ?, ?)
            ''', (device_id, status, value, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新设备状态失败：{e}")
    
    def get_device_history(self, device_id: str, days: int = 7) -> List[Dict]:
        """获取设备历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            c.execute('''
                SELECT status, value, recorded_at
                FROM device_status_history
                WHERE device_id = ? AND recorded_at >= ?
                ORDER BY recorded_at DESC
            ''', (device_id, start_date))
            
            rows = c.fetchall()
            conn.close()
            
            return [
                {
                    'status': row[0],
                    'value': row[1],
                    'recorded_at': row[2]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"获取设备历史失败：{e}")
            return []
    
    def add_energy_record(self, device_id: str, power_consumption: float):
        """添加能耗记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO energy_records (device_id, power_consumption, recorded_at)
                VALUES (?, ?, ?)
            ''', (device_id, power_consumption, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"添加能耗记录失败：{e}")
    
    def get_energy_stats(self, device_id: str = None, days: int = 7) -> Dict:
        """获取能耗统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            if device_id:
                c.execute('''
                    SELECT SUM(power_consumption), AVG(power_consumption), 
                           MIN(power_consumption), MAX(power_consumption)
                    FROM energy_records
                    WHERE device_id = ? AND recorded_at >= ?
                ''', (device_id, start_date))
            else:
                c.execute('''
                    SELECT SUM(power_consumption), AVG(power_consumption),
                           MIN(power_consumption), MAX(power_consumption)
                    FROM energy_records
                    WHERE recorded_at >= ?
                ''', (start_date,))
            
            row = c.fetchone()
            conn.close()
            
            return {
                'total': row[0] or 0,
                'average': row[1] or 0,
                'min': row[2] or 0,
                'max': row[3] or 0,
                'period': f'{days}天'
            }
        except Exception as e:
            logger.error(f"获取能耗统计失败：{e}")
            return {'total': 0, 'average': 0, 'min': 0, 'max': 0, 'period': f'{days}天'}
    
    def get_device_list(self) -> List[Dict]:
        """获取设备列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('SELECT * FROM devices ORDER BY room, device_name')
            
            rows = c.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'device_id': row[1],
                    'device_name': row[2],
                    'device_type': row[3],
                    'platform': row[4],
                    'room': row[5],
                    'is_online': bool(row[6]),
                    'created_at': row[7]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"获取设备列表失败：{e}")
            return []
    
    def get_room_stats(self) -> Dict:
        """获取房间统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT room, COUNT(*) as device_count, 
                       SUM(CASE WHEN is_online THEN 1 ELSE 0 END) as online_count
                FROM devices
                GROUP BY room
            ''')
            
            rows = c.fetchall()
            conn.close()
            
            return {
                row[0]: {
                    'device_count': row[1],
                    'online_count': row[2],
                    'offline_count': row[1] - row[2]
                }
                for row in rows
            }
        except Exception as e:
            logger.error(f"获取房间统计失败：{e}")
            return {}


# 使用示例
if __name__ == '__main__':
    service = DeviceDataService()
    
    # 添加设备
    service.add_device("MI_001", "客厅灯", "light", "mihome", "客厅")
    service.add_device("MI_002", "空调", "aircon", "mihome", "客厅")
    
    # 更新状态
    service.update_device_status("MI_001", "online", "on")
    
    # 添加能耗记录
    service.add_energy_record("MI_001", 0.5)
    
    # 获取统计
    stats = service.get_energy_stats(days=7)
    logger.info(f"能耗统计：{stats}")
    
    # 获取设备列表
    devices = service.get_device_list()
    logger.info(f"设备总数：{len(devices)}")
