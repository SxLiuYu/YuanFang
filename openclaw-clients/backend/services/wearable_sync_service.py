#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能手表数据同步服务
支持 Apple Watch (HealthKit), 华为手表, 小米手表, Garmin
"""
import logging
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    APPLE_WATCH = "apple_watch"
    HUAWEI = "huawei"
    XIAOMI = "xiaomi"
    GARMIN = "garmin"


class DataType(Enum):
    STEPS = "steps"
    HEART_RATE = "heart_rate"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    BLOOD_OXYGEN = "blood_oxygen"


@dataclass
class WearableData:
    device_id: str
    data_type: str
    value: float
    unit: str
    recorded_at: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class WearableSyncService:
    """智能手表数据同步服务"""
    
    DEVICE_PLATFORMS = {
        DeviceType.APPLE_WATCH: {
            "name": "Apple Watch",
            "api_name": "healthkit",
            "supported_data": [
                DataType.STEPS, DataType.HEART_RATE, DataType.SLEEP,
                DataType.EXERCISE, DataType.BLOOD_OXYGEN
            ]
        },
        DeviceType.HUAWEI: {
            "name": "华为手表",
            "api_name": "huawei_health",
            "supported_data": [
                DataType.STEPS, DataType.HEART_RATE, DataType.SLEEP,
                DataType.EXERCISE, DataType.BLOOD_OXYGEN
            ]
        },
        DeviceType.XIAOMI: {
            "name": "小米手表",
            "api_name": "mi_health",
            "supported_data": [
                DataType.STEPS, DataType.HEART_RATE, DataType.SLEEP,
                DataType.EXERCISE, DataType.BLOOD_OXYGEN
            ]
        },
        DeviceType.GARMIN: {
            "name": "Garmin",
            "api_name": "garmin_connect",
            "supported_data": [
                DataType.STEPS, DataType.HEART_RATE, DataType.SLEEP,
                DataType.EXERCISE, DataType.BLOOD_OXYGEN
            ]
        }
    }
    
    DATA_RANGES = {
        DataType.STEPS.value: {"min": 0, "max": 100000, "unit": "步"},
        DataType.HEART_RATE.value: {"min": 30, "max": 220, "unit": "bpm"},
        DataType.SLEEP.value: {"min": 0, "max": 24, "unit": "小时"},
        DataType.EXERCISE.value: {"min": 0, "max": 1440, "unit": "分钟"},
        DataType.BLOOD_OXYGEN.value: {"min": 70, "max": 100, "unit": "%"}
    }
    
    ANOMALY_THRESHOLDS = {
        DataType.HEART_RATE.value: {
            "low": {"threshold": 50, "severity": "warning", "message": "心率过低"},
            "high": {"threshold": 120, "severity": "warning", "message": "心率过高"},
            "critical_low": {"threshold": 40, "severity": "critical", "message": "心率危急偏低"},
            "critical_high": {"threshold": 150, "severity": "critical", "message": "心率危急偏高"}
        },
        DataType.BLOOD_OXYGEN.value: {
            "low": {"threshold": 95, "severity": "warning", "message": "血氧饱和度偏低"},
            "critical_low": {"threshold": 90, "severity": "critical", "message": "血氧饱和度危急偏低"}
        },
        DataType.SLEEP.value: {
            "low": {"threshold": 5, "severity": "info", "message": "睡眠时间偏少"},
            "high": {"threshold": 10, "severity": "info", "message": "睡眠时间偏多"}
        }
    }
    
    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        self._conn = None
        self._init_db()
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        c = self._get_conn().cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS wearable_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                device_type TEXT NOT NULL,
                device_name TEXT,
                device_model TEXT,
                firmware_version TEXT,
                last_sync TIMESTAMP,
                sync_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS wearable_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                metadata TEXT,
                recorded_at TIMESTAMP NOT NULL,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid INTEGER DEFAULT 1,
                validation_message TEXT,
                FOREIGN KEY (device_id) REFERENCES wearable_devices(device_id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS wearable_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                anomaly_type TEXT,
                severity TEXT,
                message TEXT,
                details TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES wearable_devices(device_id)
            )
        ''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_wearable_device_id ON wearable_data(device_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wearable_data_type ON wearable_data(data_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wearable_recorded_at ON wearable_data(recorded_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wearable_device_type ON wearable_devices(device_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wearable_anomaly_device ON wearable_anomalies(device_id)')
        
        self._conn.commit()
        logger.info("Wearable sync service database initialized")
    
    async def register_device(self, device_id: str, device_type: str, user_id: str = None,
                             device_name: str = None, device_model: str = None,
                             firmware_version: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            if device_type not in [dt.value for dt in DeviceType]:
                return {"error": f"不支持的设备类型: {device_type}"}
            
            now = datetime.now()
            
            c.execute('''
                INSERT INTO wearable_devices 
                (device_id, user_id, device_type, device_name, device_model, firmware_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (device_id, user_id, device_type, device_name, device_model, firmware_version, now, now))
            
            conn.commit()
            
            logger.info(f"Device registered: {device_id} ({device_type})")
            
            return {
                "success": True,
                "device_id": device_id,
                "device_type": device_type,
                "device_name": device_name,
                "user_id": user_id,
                "registered_at": now.isoformat()
            }
        
        except sqlite3.IntegrityError:
            c.execute('''
                UPDATE wearable_devices 
                SET user_id = ?, device_name = ?, device_model = ?, firmware_version = ?, updated_at = ?
                WHERE device_id = ?
            ''', (user_id, device_name, device_model, firmware_version, now, device_id))
            conn.commit()
            
            return {
                "success": True,
                "device_id": device_id,
                "message": "设备信息已更新"
            }
        
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return {"error": str(e)}
    
    async def unregister_device(self, device_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM wearable_devices WHERE device_id = ?', (device_id,))
        
        if c.rowcount == 0:
            return {"error": "设备不存在"}
        
        c.execute('DELETE FROM wearable_data WHERE device_id = ?', (device_id,))
        c.execute('DELETE FROM wearable_anomalies WHERE device_id = ?', (device_id,))
        
        conn.commit()
        
        logger.info(f"Device unregistered: {device_id}")
        return {"success": True, "message": f"设备 {device_id} 已注销"}
    
    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM wearable_devices WHERE device_id = ?', (device_id,))
        row = c.fetchone()
        
        if row:
            return {
                "device_id": row['device_id'],
                "user_id": row['user_id'],
                "device_type": row['device_type'],
                "device_name": row['device_name'],
                "device_model": row['device_model'],
                "firmware_version": row['firmware_version'],
                "last_sync": row['last_sync'],
                "sync_token": row['sync_token'],
                "created_at": row['created_at']
            }
        
        return None
    
    async def list_devices(self, user_id: str = None, device_type: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        sql = 'SELECT * FROM wearable_devices'
        params = []
        conditions = []
        
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        
        if device_type:
            conditions.append('device_type = ?')
            params.append(device_type)
        
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        
        sql += ' ORDER BY created_at DESC'
        
        c.execute(sql, tuple(params))
        
        devices = []
        for row in c.fetchall():
            devices.append({
                "device_id": row['device_id'],
                "user_id": row['user_id'],
                "device_type": row['device_type'],
                "device_name": row['device_name'],
                "device_model": row['device_model'],
                "last_sync": row['last_sync']
            })
        
        return devices
    
    def validate_data(self, data: WearableData) -> Tuple[bool, Optional[str]]:
        if data.data_type not in self.DATA_RANGES:
            return False, f"未知的数据类型: {data.data_type}"
        
        data_range = self.DATA_RANGES[data.data_type]
        
        if data.value < data_range["min"]:
            return False, f"数值 {data.value} 低于最小值 {data_range['min']}"
        
        if data.value > data_range["max"]:
            return False, f"数值 {data.value} 超过最大值 {data_range['max']}"
        
        return True, None
    
    def detect_anomaly(self, data: WearableData, historical_values: List[float] = None) -> AnomalyResult:
        if data.data_type not in self.ANOMALY_THRESHOLDS:
            return AnomalyResult(is_anomaly=False)
        
        thresholds = self.ANOMALY_THRESHOLDS[data.data_type]
        
        for threshold_name, threshold_config in thresholds.items():
            if "low" in threshold_name or "critical_low" in threshold_name:
                if data.value < threshold_config["threshold"]:
                    return AnomalyResult(
                        is_anomaly=True,
                        anomaly_type=f"{data.data_type}_{threshold_name}",
                        severity=threshold_config["severity"],
                        message=threshold_config["message"],
                        details={"value": data.value, "threshold": threshold_config["threshold"]}
                    )
            elif "high" in threshold_name or "critical_high" in threshold_name:
                if data.value > threshold_config["threshold"]:
                    return AnomalyResult(
                        is_anomaly=True,
                        anomaly_type=f"{data.data_type}_{threshold_name}",
                        severity=threshold_config["severity"],
                        message=threshold_config["message"],
                        details={"value": data.value, "threshold": threshold_config["threshold"]}
                    )
        
        if historical_values and len(historical_values) >= 5:
            avg = statistics.mean(historical_values)
            std = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
            
            if std > 0:
                z_score = abs(data.value - avg) / std
                if z_score > 3:
                    return AnomalyResult(
                        is_anomaly=True,
                        anomaly_type="statistical_outlier",
                        severity="warning",
                        message=f"{data.data_type} 数值异常偏离历史均值",
                        details={
                            "value": data.value,
                            "historical_mean": round(avg, 2),
                            "z_score": round(z_score, 2)
                        }
                    )
        
        return AnomalyResult(is_anomaly=False)
    
    async def sync_data(self, device_id: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        device = await self.get_device(device_id)
        if not device:
            return {"error": f"设备未注册: {device_id}"}
        
        conn = self._get_conn()
        c = conn.cursor()
        
        synced_count = 0
        anomaly_count = 0
        invalid_count = 0
        errors = []
        
        for data_item in data_list:
            try:
                data_type = data_item.get("data_type")
                value = data_item.get("value")
                unit = data_item.get("unit")
                recorded_at_str = data_item.get("recorded_at")
                metadata = data_item.get("metadata")
                
                if data_type is None or value is None:
                    invalid_count += 1
                    continue
                
                if recorded_at_str:
                    recorded_at = datetime.fromisoformat(recorded_at_str.replace('Z', '+00:00'))
                else:
                    recorded_at = datetime.now()
                
                wearable_data = WearableData(
                    device_id=device_id,
                    data_type=data_type,
                    value=float(value),
                    unit=unit or self.DATA_RANGES.get(data_type, {}).get("unit", ""),
                    recorded_at=recorded_at,
                    metadata=metadata
                )
                
                is_valid, validation_msg = self.validate_data(wearable_data)
                
                historical_values = await self._get_recent_values(device_id, data_type, 30)
                anomaly_result = self.detect_anomaly(wearable_data, historical_values)
                
                now = datetime.now()
                
                c.execute('''
                    INSERT INTO wearable_data 
                    (device_id, data_type, value, unit, metadata, recorded_at, synced_at, is_valid, validation_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id, data_type, wearable_data.value, wearable_data.unit,
                    json.dumps(metadata) if metadata else None,
                    recorded_at, now, 1 if is_valid else 0, validation_msg
                ))
                
                if anomaly_result.is_anomaly:
                    anomaly_count += 1
                    c.execute('''
                        INSERT INTO wearable_anomalies 
                        (device_id, data_type, anomaly_type, severity, message, details, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        device_id, data_type, anomaly_result.anomaly_type,
                        anomaly_result.severity, anomaly_result.message,
                        json.dumps(anomaly_result.details) if anomaly_result.details else None,
                        now
                    ))
                
                synced_count += 1
            
            except Exception as e:
                errors.append(str(e))
                invalid_count += 1
        
        c.execute('''
            UPDATE wearable_devices 
            SET last_sync = ?, updated_at = ?
            WHERE device_id = ?
        ''', (datetime.now(), datetime.now(), device_id))
        
        conn.commit()
        
        logger.info(f"Data synced for {device_id}: {synced_count} records, {anomaly_count} anomalies")
        
        return {
            "success": True,
            "device_id": device_id,
            "synced_count": synced_count,
            "anomaly_count": anomaly_count,
            "invalid_count": invalid_count,
            "errors": errors[:10] if errors else None
        }
    
    async def _get_recent_values(self, device_id: str, data_type: str, limit: int = 30) -> List[float]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT value FROM wearable_data 
            WHERE device_id = ? AND data_type = ? AND is_valid = 1
            ORDER BY recorded_at DESC
            LIMIT ?
        ''', (device_id, data_type, limit))
        
        return [row[0] for row in c.fetchall()]
    
    async def get_data(self, device_id: str, data_type: str = None, 
                       start_time: datetime = None, end_time: datetime = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        sql = 'SELECT * FROM wearable_data WHERE device_id = ?'
        params = [device_id]
        
        if data_type:
            sql += ' AND data_type = ?'
            params.append(data_type)
        
        if start_time:
            sql += ' AND recorded_at >= ?'
            params.append(start_time)
        
        if end_time:
            sql += ' AND recorded_at <= ?'
            params.append(end_time)
        
        sql += ' ORDER BY recorded_at DESC LIMIT ?'
        params.append(limit)
        
        c.execute(sql, tuple(params))
        
        records = []
        for row in c.fetchall():
            records.append({
                "id": row['id'],
                "device_id": row['device_id'],
                "data_type": row['data_type'],
                "value": row['value'],
                "unit": row['unit'],
                "metadata": json.loads(row['metadata']) if row['metadata'] else None,
                "recorded_at": row['recorded_at'],
                "synced_at": row['synced_at'],
                "is_valid": bool(row['is_valid']),
                "validation_message": row['validation_message']
            })
        
        return records
    
    async def analyze_trends(self, device_id: str, data_type: str, days: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_time = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT value, recorded_at FROM wearable_data 
            WHERE device_id = ? AND data_type = ? AND is_valid = 1 AND recorded_at >= ?
            ORDER BY recorded_at ASC
        ''', (device_id, data_type, start_time))
        
        rows = c.fetchall()
        
        if not rows:
            return {
                "device_id": device_id,
                "data_type": data_type,
                "period_days": days,
                "message": "无足够数据进行分析"
            }
        
        values = [row[0] for row in rows]
        
        trend = "stable"
        if len(values) >= 3:
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2) if len(values)//2 > 0 else values[0]
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg != 0 else 0
            
            if change_percent > 10:
                trend = "increasing"
            elif change_percent < -10:
                trend = "decreasing"
        
        daily_data = {}
        for row in rows:
            date_str = row[1][:10] if isinstance(row[1], str) else row[1].strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = []
            daily_data[date_str].append(row[0])
        
        daily_summary = []
        for date_str, day_values in sorted(daily_data.items()):
            daily_summary.append({
                "date": date_str,
                "count": len(day_values),
                "sum": round(sum(day_values), 2),
                "avg": round(sum(day_values) / len(day_values), 2),
                "min": min(day_values),
                "max": max(day_values)
            })
        
        return {
            "device_id": device_id,
            "data_type": data_type,
            "period_days": days,
            "total_records": len(values),
            "statistics": {
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 2),
                "median": statistics.median(values),
                "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0
            },
            "trend": trend,
            "daily_summary": daily_summary,
            "analysis_time": datetime.now().isoformat()
        }
    
    async def get_anomalies(self, device_id: str = None, severity: str = None,
                           resolved: bool = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        sql = 'SELECT * FROM wearable_anomalies'
        conditions = []
        params = []
        
        if device_id:
            conditions.append('device_id = ?')
            params.append(device_id)
        
        if severity:
            conditions.append('severity = ?')
            params.append(severity)
        
        if resolved is not None:
            conditions.append('is_resolved = ?')
            params.append(1 if resolved else 0)
        
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        
        sql += ' ORDER BY detected_at DESC LIMIT ?'
        params.append(limit)
        
        c.execute(sql, tuple(params))
        
        anomalies = []
        for row in c.fetchall():
            anomalies.append({
                "id": row['id'],
                "device_id": row['device_id'],
                "data_type": row['data_type'],
                "anomaly_type": row['anomaly_type'],
                "severity": row['severity'],
                "message": row['message'],
                "details": json.loads(row['details']) if row['details'] else None,
                "detected_at": row['detected_at'],
                "is_resolved": bool(row['is_resolved']),
                "resolved_at": row['resolved_at']
            })
        
        return anomalies
    
    async def resolve_anomaly(self, anomaly_id: int) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        now = datetime.now()
        c.execute('''
            UPDATE wearable_anomalies 
            SET is_resolved = 1, resolved_at = ?
            WHERE id = ?
        ''', (now, anomaly_id))
        
        if c.rowcount == 0:
            return {"error": "异常记录不存在"}
        
        conn.commit()
        
        return {"success": True, "message": f"异常 {anomaly_id} 已标记为已解决"}
    
    async def get_device_summary(self, device_id: str) -> Dict[str, Any]:
        device = await self.get_device(device_id)
        if not device:
            return {"error": "设备不存在"}
        
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT data_type, COUNT(*) as count, MAX(recorded_at) as latest_record
            FROM wearable_data 
            WHERE device_id = ? AND is_valid = 1
            GROUP BY data_type
        ''', (device_id,))
        
        data_summary = {}
        for row in c.fetchall():
            data_summary[row[0]] = {
                "count": row[1],
                "latest_record": row[2]
            }
        
        c.execute('''
            SELECT COUNT(*) FROM wearable_anomalies 
            WHERE device_id = ? AND is_resolved = 0
        ''', (device_id,))
        
        unresolved_anomalies = c.fetchone()[0]
        
        c.execute('''
            SELECT COUNT(*) FROM wearable_data 
            WHERE device_id = ?
        ''', (device_id,))
        
        total_records = c.fetchone()[0]
        
        return {
            "device": device,
            "total_records": total_records,
            "data_summary": data_summary,
            "unresolved_anomalies": unresolved_anomalies,
            "summary_time": datetime.now().isoformat()
        }
    
    async def get_health_report(self, device_id: str, days: int = 7) -> Dict[str, Any]:
        device = await self.get_device(device_id)
        if not device:
            return {"error": "设备不存在"}
        
        report = {
            "device": device,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "data_types": {}
        }
        
        for data_type in DataType:
            trend_analysis = await self.analyze_trends(device_id, data_type.value, days)
            if "statistics" in trend_analysis:
                report["data_types"][data_type.value] = trend_analysis
        
        recent_anomalies = await self.get_anomalies(device_id=device_id, limit=10)
        report["recent_anomalies"] = recent_anomalies
        
        return report
    
    async def sync_from_platform(self, device_id: str, platform: str, 
                                  credentials: Dict[str, Any]) -> Dict[str, Any]:
        device = await self.get_device(device_id)
        if not device:
            return {"error": "设备未注册"}
        
        if platform not in [dt.value for dt in DeviceType]:
            return {"error": f"不支持的平台: {platform}"}
        
        logger.info(f"Simulating sync from {platform} for device {device_id}")
        
        return {
            "success": True,
            "device_id": device_id,
            "platform": platform,
            "message": "同步接口已准备，需配置实际API密钥",
            "note": "请提供实际的API凭证以完成同步"
        }
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[WearableSyncService] = None


def get_service() -> WearableSyncService:
    global _service_instance
    if _service_instance is None:
        _service_instance = WearableSyncService()
    return _service_instance


async def register_device(device_id: str, device_type: str, **kwargs) -> Dict[str, Any]:
    return await get_service().register_device(device_id, device_type, **kwargs)


async def sync_data(device_id: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    return await get_service().sync_data(device_id, data_list)


async def get_data(device_id: str, **kwargs) -> List[Dict[str, Any]]:
    return await get_service().get_data(device_id, **kwargs)


async def analyze_trends(device_id: str, data_type: str, days: int = 7) -> Dict[str, Any]:
    return await get_service().analyze_trends(device_id, data_type, days)


async def get_anomalies(**kwargs) -> List[Dict[str, Any]]:
    return await get_service().get_anomalies(**kwargs)


async def get_health_report(device_id: str, days: int = 7) -> Dict[str, Any]:
    return await get_service().get_health_report(device_id, days)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = WearableSyncService(':memory:')
        
        print("=== 智能手表数据同步服务测试 ===\n")
        
        print("1. 注册设备...")
        result = await service.register_device(
            device_id="apple_watch_001",
            device_type="apple_watch",
            user_id="user_001",
            device_name="我的Apple Watch",
            device_model="Series 8"
        )
        print(f"   注册结果: {result}")
        
        now = datetime.now()
        
        print("\n2. 同步步数数据...")
        sync_result = await service.sync_data("apple_watch_001", [
            {"data_type": "steps", "value": 8500, "unit": "步", "recorded_at": (now - timedelta(days=0)).isoformat()},
            {"data_type": "steps", "value": 10200, "unit": "步", "recorded_at": (now - timedelta(days=1)).isoformat()},
            {"data_type": "steps", "value": 6800, "unit": "步", "recorded_at": (now - timedelta(days=2)).isoformat()},
        ])
        print(f"   同步结果: {sync_result}")
        
        print("\n3. 同步心率数据...")
        sync_result = await service.sync_data("apple_watch_001", [
            {"data_type": "heart_rate", "value": 72, "unit": "bpm", "recorded_at": (now - timedelta(hours=2)).isoformat()},
            {"data_type": "heart_rate", "value": 135, "unit": "bpm", "recorded_at": (now - timedelta(hours=1)).isoformat(), "metadata": {"activity": "运动中"}},
            {"data_type": "heart_rate", "value": 68, "unit": "bpm", "recorded_at": (now - timedelta(days=1)).isoformat()},
            {"data_type": "heart_rate", "value": 45, "unit": "bpm", "recorded_at": (now - timedelta(days=1, hours=8)).isoformat(), "metadata": {"state": "睡眠中"}},
        ])
        print(f"   同步结果: {sync_result}")
        
        print("\n4. 同步血氧数据...")
        sync_result = await service.sync_data("apple_watch_001", [
            {"data_type": "blood_oxygen", "value": 98, "unit": "%", "recorded_at": (now - timedelta(hours=3)).isoformat()},
            {"data_type": "blood_oxygen", "value": 88, "unit": "%", "recorded_at": (now - timedelta(hours=5)).isoformat()},
        ])
        print(f"   同步结果: {sync_result}")
        
        print("\n5. 同步睡眠数据...")
        sync_result = await service.sync_data("apple_watch_001", [
            {"data_type": "sleep", "value": 7.5, "unit": "小时", "recorded_at": (now - timedelta(hours=8)).isoformat()},
            {"data_type": "sleep", "value": 6.0, "unit": "小时", "recorded_at": (now - timedelta(days=1, hours=8)).isoformat()},
            {"data_type": "sleep", "value": 8.2, "unit": "小时", "recorded_at": (now - timedelta(days=2, hours=8)).isoformat()},
        ])
        print(f"   同步结果: {sync_result}")
        
        print("\n6. 查询数据...")
        data = await service.get_data("apple_watch_001", data_type="steps", limit=10)
        print(f"   步数数据: {len(data)} 条")
        
        print("\n7. 分析趋势...")
        trend = await service.analyze_trends("apple_watch_001", "steps", days=7)
        print(f"   趋势分析: {trend.get('trend', 'N/A')}")
        print(f"   统计数据: {trend.get('statistics')}")
        
        print("\n8. 获取异常...")
        anomalies = await service.get_anomalies(device_id="apple_watch_001")
        print(f"   异常数量: {len(anomalies)}")
        for a in anomalies:
            print(f"   - [{a['severity']}] {a['message']}: {a['details']}")
        
        print("\n9. 获取设备摘要...")
        summary = await service.get_device_summary("apple_watch_001")
        print(f"   总记录数: {summary['total_records']}")
        print(f"   未解决异常: {summary['unresolved_anomalies']}")
        
        print("\n10. 获取健康报告...")
        report = await service.get_health_report("apple_watch_001", days=7)
        print(f"   报告生成时间: {report['generated_at']}")
        print(f"   数据类型: {list(report['data_types'].keys())}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())