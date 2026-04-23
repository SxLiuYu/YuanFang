#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw - 硬件集成服务
支持智能手表、智能音箱、健康设备、蓝牙设备

Author: 于金泽
Version: 1.0.0
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

class DeviceRegister(BaseModel):
    name: str
    type: str  # "smart_watch", "smart_speaker", "health_device", "bluetooth"
    brand: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DeviceControl(BaseModel):
    device_id: str
    action: str
    params: Optional[Dict[str, Any]] = None

class WatchDataSync(BaseModel):
    device_id: str
    user_id: str
    timestamp: datetime
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    sleep_duration: Optional[int] = None
    calories: Optional[int] = None
    blood_oxygen: Optional[float] = None
    blood_pressure: Optional[Dict[str, int]] = None

class SpeakerCommand(BaseModel):
    device_id: str
    command: str  # "play", "pause", "volume_up", "volume_down", "speak"
    content: Optional[str] = None
    volume: Optional[int] = None

class BluetoothScanResult(BaseModel):
    device_id: str
    name: str
    type: str
    rssi: int
    is_paired: bool

class HardwareDevice(BaseModel):
    id: str
    name: str
    type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    status: str = "offline"  # "online", "offline", "pairing"
    battery_level: Optional[int] = None
    last_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

# ═══════════════════════════════════════════════════════════════
# 硬件服务类
# ═══════════════════════════════════════════════════════════════

class HardwareService:
    """硬件集成服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent.parent / "data" / "hardware.db")
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 设备表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardware_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                status TEXT DEFAULT 'offline',
                battery_level INTEGER,
                last_sync DATETIME,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 手表数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watch_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                heart_rate INTEGER,
                steps INTEGER,
                sleep_duration INTEGER,
                calories INTEGER,
                blood_oxygen REAL,
                blood_pressure TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES hardware_devices(id)
            )
        """)
        
        # 设备操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                action TEXT NOT NULL,
                params TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES hardware_devices(id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_type ON hardware_devices(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_status ON hardware_devices(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watch_device ON watch_data(device_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watch_user ON watch_data(user_id)")
        
        conn.commit()
        conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 设备管理
    # ═══════════════════════════════════════════════════════════════
    
    async def register_device(self, request: DeviceRegister) -> Dict[str, Any]:
        """注册设备"""
        device_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO hardware_devices (id, name, type, brand, model, metadata, status)
                VALUES (?, ?, ?, ?, ?, ?, 'online')
            """, (device_id, request.name, request.type, request.brand, request.model,
                  json.dumps(request.metadata or {}, ensure_ascii=False)))
            
            conn.commit()
            
            return {
                "success": True,
                "device_id": device_id,
                "message": f"设备 '{request.name}' 注册成功"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"注册设备失败: {e}")
            return {"success": False, "message": f"注册失败: {str(e)}"}
        finally:
            conn.close()
    
    async def get_devices(self, device_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        """获取设备列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM hardware_devices WHERE 1=1"
            params = []
            
            if device_type:
                query += " AND type = ?"
                params.append(device_type)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            devices = []
            for row in rows:
                devices.append({
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "brand": row[3],
                    "model": row[4],
                    "status": row[5],
                    "battery_level": row[6],
                    "last_sync": row[7],
                    "metadata": json.loads(row[8]) if row[8] else {},
                    "created_at": row[9]
                })
            
            return devices
        finally:
            conn.close()
    
    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """获取设备详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM hardware_devices WHERE id = ?", (device_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "brand": row[3],
                "model": row[4],
                "status": row[5],
                "battery_level": row[6],
                "last_sync": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
                "created_at": row[9]
            }
        finally:
            conn.close()
    
    async def update_device_status(self, device_id: str, status: str, battery_level: int = None) -> Dict[str, Any]:
        """更新设备状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if battery_level is not None:
                cursor.execute("""
                    UPDATE hardware_devices 
                    SET status = ?, battery_level = ?, last_sync = ?
                    WHERE id = ?
                """, (status, battery_level, datetime.now(), device_id))
            else:
                cursor.execute("""
                    UPDATE hardware_devices 
                    SET status = ?, last_sync = ?
                    WHERE id = ?
                """, (status, datetime.now(), device_id))
            
            conn.commit()
            return {"success": True, "message": "设备状态已更新"}
        except Exception as e:
            conn.rollback()
            logger.error(f"更新设备状态失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
        finally:
            conn.close()
    
    async def delete_device(self, device_id: str) -> Dict[str, Any]:
        """删除设备"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM device_logs WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM watch_data WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM hardware_devices WHERE id = ?", (device_id,))
            
            conn.commit()
            return {"success": True, "message": "设备已删除"}
        except Exception as e:
            conn.rollback()
            logger.error(f"删除设备失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 智能手表
    # ═══════════════════════════════════════════════════════════════
    
    async def sync_watch_data(self, request: WatchDataSync) -> Dict[str, Any]:
        """同步智能手表数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证设备存在
            cursor.execute("SELECT id FROM hardware_devices WHERE id = ? AND type = 'smart_watch'", 
                          (request.device_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "智能手表设备不存在"}
            
            # 插入数据
            cursor.execute("""
                INSERT INTO watch_data 
                (device_id, user_id, timestamp, heart_rate, steps, sleep_duration, 
                 calories, blood_oxygen, blood_pressure)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (request.device_id, request.user_id, request.timestamp,
                  request.heart_rate, request.steps, request.sleep_duration,
                  request.calories, request.blood_oxygen,
                  json.dumps(request.blood_pressure) if request.blood_pressure else None))
            
            # 更新设备最后同步时间
            cursor.execute("""
                UPDATE hardware_devices SET last_sync = ?, status = 'online'
                WHERE id = ?
            """, (datetime.now(), request.device_id))
            
            conn.commit()
            
            return {
                "success": True,
                "message": "数据同步成功",
                "data": {
                    "heart_rate": request.heart_rate,
                    "steps": request.steps,
                    "sleep_duration": request.sleep_duration
                }
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"同步手表数据失败: {e}")
            return {"success": False, "message": f"同步失败: {str(e)}"}
        finally:
            conn.close()
    
    async def get_watch_data(self, device_id: str, user_id: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """获取智能手表数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT device_id, user_id, timestamp, heart_rate, steps, 
                       sleep_duration, calories, blood_oxygen, blood_pressure
                FROM watch_data
                WHERE device_id = ? AND timestamp >= datetime('now', ?)
            """
            params = [device_id, f'-{days} days']
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    "device_id": row[0],
                    "user_id": row[1],
                    "timestamp": row[2],
                    "heart_rate": row[3],
                    "steps": row[4],
                    "sleep_duration": row[5],
                    "calories": row[6],
                    "blood_oxygen": row[7],
                    "blood_pressure": json.loads(row[8]) if row[8] else None
                })
            
            return data
        finally:
            conn.close()
    
    async def get_health_summary(self, device_id: str, user_id: str) -> Dict[str, Any]:
        """获取健康数据摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取最近7天的平均数据
            cursor.execute("""
                SELECT 
                    AVG(heart_rate) as avg_heart_rate,
                    MAX(heart_rate) as max_heart_rate,
                    MIN(heart_rate) as min_heart_rate,
                    SUM(steps) as total_steps,
                    AVG(steps) as avg_steps,
                    AVG(sleep_duration) as avg_sleep,
                    SUM(calories) as total_calories,
                    AVG(blood_oxygen) as avg_blood_oxygen
                FROM watch_data
                WHERE device_id = ? AND user_id = ?
                AND timestamp >= datetime('now', '-7 days')
            """, (device_id, user_id))
            
            row = cursor.fetchone()
            
            return {
                "avg_heart_rate": round(row[0], 1) if row[0] else None,
                "max_heart_rate": row[1],
                "min_heart_rate": row[2],
                "total_steps": row[3],
                "avg_steps": round(row[4], 1) if row[4] else None,
                "avg_sleep": round(row[5], 1) if row[5] else None,
                "total_calories": row[6],
                "avg_blood_oxygen": round(row[7], 1) if row[7] else None,
                "period_days": 7
            }
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 智能音箱
    # ═══════════════════════════════════════════════════════════════
    
    async def send_speaker_command(self, request: SpeakerCommand) -> Dict[str, Any]:
        """发送智能音箱命令"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证设备
            cursor.execute("SELECT id, name FROM hardware_devices WHERE id = ? AND type = 'smart_speaker'",
                          (request.device_id,))
            device = cursor.fetchone()
            
            if not device:
                return {"success": False, "message": "智能音箱设备不存在"}
            
            # 记录命令日志
            cursor.execute("""
                INSERT INTO device_logs (device_id, action, params, result, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (request.device_id, request.command, 
                  json.dumps({"content": request.content, "volume": request.volume}),
                  "success", datetime.now()))
            
            conn.commit()
            
            # 模拟命令执行（实际应调用设备API）
            command_responses = {
                "play": "开始播放",
                "pause": "已暂停",
                "volume_up": "音量增加",
                "volume_down": "音量降低",
                "speak": f"正在播放: {request.content}"
            }
            
            return {
                "success": True,
                "message": command_responses.get(request.command, "命令已执行"),
                "device_name": device[1]
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"发送音箱命令失败: {e}")
            return {"success": False, "message": f"命令发送失败: {str(e)}"}
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 蓝牙设备
    # ═══════════════════════════════════════════════════════════════
    
    async def scan_bluetooth_devices(self) -> List[Dict[str, Any]]:
        """扫描蓝牙设备（模拟）"""
        # 模拟扫描结果
        mock_devices = [
            {"id": "bt_001", "name": "小米手环8", "type": "smart_watch", "rssi": -45, "is_paired": False},
            {"id": "bt_002", "name": "小爱音箱Pro", "type": "smart_speaker", "rssi": -60, "is_paired": True},
            {"id": "bt_003", "name": "华为体脂秤", "type": "health_device", "rssi": -70, "is_paired": False},
        ]
        
        return mock_devices
    
    async def pair_bluetooth_device(self, device_id: str, device_name: str, device_type: str) -> Dict[str, Any]:
        """配对蓝牙设备"""
        # 注册设备
        request = DeviceRegister(
            name=device_name,
            type=device_type,
            brand="蓝牙设备"
        )
        
        result = await self.register_device(request)
        
        if result["success"]:
            result["message"] = f"设备 '{device_name}' 配对成功"
        
        return result
    
    async def control_device(self, request: DeviceControl) -> Dict[str, Any]:
        """控制设备"""
        device = await self.get_device(request.device_id)
        
        if not device:
            return {"success": False, "message": "设备不存在"}
        
        device_type = device["type"]
        
        if device_type == "smart_speaker":
            speaker_cmd = SpeakerCommand(
                device_id=request.device_id,
                action=request.action,
                content=request.params.get("content") if request.params else None,
                volume=request.params.get("volume") if request.params else None
            )
            return await self.send_speaker_command(speaker_cmd)
        
        # 通用设备控制
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO device_logs (device_id, action, params, result, timestamp)
                VALUES (?, ?, ?, 'success', ?)
            """, (request.device_id, request.action, 
                  json.dumps(request.params) if request.params else None,
                  datetime.now()))
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"设备 '{device['name']}' 已执行 {request.action}",
                "device": device
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"控制设备失败: {e}")
            return {"success": False, "message": f"控制失败: {str(e)}"}
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════
# 服务实例
# ═══════════════════════════════════════════════════════════════

hardware_service = HardwareService()