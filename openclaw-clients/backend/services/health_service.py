#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健康档案服务 - SQLite持久化版本"""
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HealthService:
    """健康档案服务"""
    
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
            CREATE TABLE IF NOT EXISTS health_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT UNIQUE,
                member_name TEXT NOT NULL,
                gender TEXT,
                birth_date TEXT,
                height REAL,
                blood_type TEXT,
                created_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS weight_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                weight REAL,
                bmi REAL,
                note TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS blood_pressure_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                systolic INTEGER,
                diastolic INTEGER,
                pulse INTEGER,
                note TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS blood_glucose_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                glucose REAL,
                measure_type TEXT,
                note TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS exercise_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                exercise_type TEXT,
                duration_minutes INTEGER,
                calories INTEGER,
                distance_km REAL,
                note TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_weight_profile ON weight_records(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bp_profile ON blood_pressure_records(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_glucose_profile ON blood_glucose_records(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exercise_profile ON exercise_records(profile_id)')
        self._conn.commit()
        logger.info("Health service database initialized")
    
    async def create_profile(self, member_name: str, gender: str = None, 
                            birth_date: str = None, height: float = None,
                            blood_type: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            profile_id = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            now = datetime.now()
            
            c.execute('''
                INSERT INTO health_profiles 
                (profile_id, member_name, gender, birth_date, height, blood_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, member_name, gender, birth_date, height, blood_type, now))
            
            conn.commit()
            
            logger.info(f"Health profile created: {member_name} (ID: {profile_id})")
            
            return {
                "id": profile_id,
                "member_name": member_name,
                "gender": gender,
                "birth_date": birth_date,
                "height": height,
                "blood_type": blood_type,
                "created_at": now.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to create health profile: {e}")
            return {"error": str(e)}
    
    async def get_profile(self, profile_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM health_profiles WHERE profile_id = ?', (profile_id,))
        row = c.fetchone()
        
        if row:
            return {
                "id": row['profile_id'],
                "member_name": row['member_name'],
                "gender": row['gender'],
                "birth_date": row['birth_date'],
                "height": row['height'],
                "blood_type": row['blood_type'],
                "created_at": row['created_at']
            }
        
        return {"error": "Profile not found"}
    
    async def list_profiles(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM health_profiles ORDER BY created_at DESC')
        
        profiles = []
        for row in c.fetchall():
            profiles.append({
                "id": row['profile_id'],
                "member_name": row['member_name'],
                "gender": row['gender'],
                "birth_date": row['birth_date'],
                "height": row['height'],
                "blood_type": row['blood_type'],
                "created_at": row['created_at']
            })
        
        return profiles
    
    async def update_profile(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        allowed_fields = ['member_name', 'gender', 'birth_date', 'height', 'blood_type']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return {"error": "No valid fields to update"}
        
        conn = self._get_conn()
        c = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [profile_id]
        
        c.execute(f"UPDATE health_profiles SET {set_clause} WHERE profile_id = ?", values)
        
        if c.rowcount == 0:
            return {"error": "Profile not found"}
        
        conn.commit()
        logger.info(f"Health profile updated: {profile_id}")
        
        return await self.get_profile(profile_id)
    
    async def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM health_profiles WHERE profile_id = ?', (profile_id,))
        
        if c.rowcount == 0:
            return {"error": "Profile not found"}
        
        c.execute('DELETE FROM weight_records WHERE profile_id = ?', (profile_id,))
        c.execute('DELETE FROM blood_pressure_records WHERE profile_id = ?', (profile_id,))
        c.execute('DELETE FROM blood_glucose_records WHERE profile_id = ?', (profile_id,))
        c.execute('DELETE FROM exercise_records WHERE profile_id = ?', (profile_id,))
        
        conn.commit()
        
        logger.info(f"Health profile deleted: {profile_id}")
        return {"success": True, "message": f"Profile {profile_id} and all records deleted"}
    
    async def record_weight(self, profile_id: str, weight: float, note: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT height FROM health_profiles WHERE profile_id = ?', (profile_id,))
        row = c.fetchone()
        
        if not row:
            return {"error": "Profile not found"}
        
        height = row['height']
        bmi = None
        if height and height > 0:
            height_m = height / 100
            bmi = round(weight / (height_m * height_m), 1)
        
        now = datetime.now()
        
        c.execute('''
            INSERT INTO weight_records (profile_id, weight, bmi, note, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (profile_id, weight, bmi, note, now))
        
        conn.commit()
        
        logger.info(f"Weight recorded for {profile_id}: {weight}kg, BMI: {bmi}")
        
        return {
            "profile_id": profile_id,
            "weight": weight,
            "bmi": bmi,
            "note": note,
            "recorded_at": now.isoformat()
        }
    
    async def record_blood_pressure(self, profile_id: str, systolic: int, diastolic: int,
                                    pulse: int = None, note: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM health_profiles WHERE profile_id = ?', (profile_id,))
        if not c.fetchone():
            return {"error": "Profile not found"}
        
        now = datetime.now()
        
        c.execute('''
            INSERT INTO blood_pressure_records 
            (profile_id, systolic, diastolic, pulse, note, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (profile_id, systolic, diastolic, pulse, note, now))
        
        conn.commit()
        
        status = self._evaluate_blood_pressure(systolic, diastolic)
        
        logger.info(f"Blood pressure recorded for {profile_id}: {systolic}/{diastolic}")
        
        return {
            "profile_id": profile_id,
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "status": status,
            "note": note,
            "recorded_at": now.isoformat()
        }
    
    def _evaluate_blood_pressure(self, systolic: int, diastolic: int) -> str:
        if systolic < 90 or diastolic < 60:
            return "偏低"
        elif systolic < 120 and diastolic < 80:
            return "正常"
        elif systolic < 140 or diastolic < 90:
            return "正常高值"
        elif systolic < 160 or diastolic < 100:
            return "高血压1级"
        elif systolic < 180 or diastolic < 110:
            return "高血压2级"
        else:
            return "高血压3级"
    
    async def record_blood_glucose(self, profile_id: str, glucose: float,
                                   measure_type: str = "fasting", note: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM health_profiles WHERE profile_id = ?', (profile_id,))
        if not c.fetchone():
            return {"error": "Profile not found"}
        
        now = datetime.now()
        
        c.execute('''
            INSERT INTO blood_glucose_records 
            (profile_id, glucose, measure_type, note, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (profile_id, glucose, measure_type, note, now))
        
        conn.commit()
        
        status = self._evaluate_blood_glucose(glucose, measure_type)
        
        logger.info(f"Blood glucose recorded for {profile_id}: {glucose}mmol/L")
        
        return {
            "profile_id": profile_id,
            "glucose": glucose,
            "measure_type": measure_type,
            "status": status,
            "note": note,
            "recorded_at": now.isoformat()
        }
    
    def _evaluate_blood_glucose(self, glucose: float, measure_type: str) -> str:
        if measure_type == "fasting":
            if glucose < 3.9:
                return "偏低"
            elif glucose < 6.1:
                return "正常"
            elif glucose < 7.0:
                return "空腹血糖受损"
            else:
                return "偏高"
        else:
            if glucose < 3.9:
                return "偏低"
            elif glucose < 7.8:
                return "正常"
            elif glucose < 11.1:
                return "糖耐量异常"
            else:
                return "偏高"
    
    async def record_exercise(self, profile_id: str, exercise_type: str,
                             duration_minutes: int, calories: int = None,
                             distance_km: float = None, note: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM health_profiles WHERE profile_id = ?', (profile_id,))
        if not c.fetchone():
            return {"error": "Profile not found"}
        
        now = datetime.now()
        
        c.execute('''
            INSERT INTO exercise_records 
            (profile_id, exercise_type, duration_minutes, calories, distance_km, note, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (profile_id, exercise_type, duration_minutes, calories, distance_km, note, now))
        
        conn.commit()
        
        logger.info(f"Exercise recorded for {profile_id}: {exercise_type} {duration_minutes}min")
        
        return {
            "profile_id": profile_id,
            "exercise_type": exercise_type,
            "duration_minutes": duration_minutes,
            "calories": calories,
            "distance_km": distance_km,
            "note": note,
            "recorded_at": now.isoformat()
        }
    
    async def get_weight_history(self, profile_id: str, days: int = 30) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT * FROM weight_records 
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, start_date))
        
        records = []
        for row in c.fetchall():
            records.append({
                "weight": row['weight'],
                "bmi": row['bmi'],
                "note": row['note'],
                "recorded_at": row['recorded_at']
            })
        
        return records
    
    async def get_blood_pressure_history(self, profile_id: str, days: int = 30) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT * FROM blood_pressure_records 
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, start_date))
        
        records = []
        for row in c.fetchall():
            records.append({
                "systolic": row['systolic'],
                "diastolic": row['diastolic'],
                "pulse": row['pulse'],
                "note": row['note'],
                "recorded_at": row['recorded_at']
            })
        
        return records
    
    async def get_blood_glucose_history(self, profile_id: str, days: int = 30) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT * FROM blood_glucose_records 
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, start_date))
        
        records = []
        for row in c.fetchall():
            records.append({
                "glucose": row['glucose'],
                "measure_type": row['measure_type'],
                "note": row['note'],
                "recorded_at": row['recorded_at']
            })
        
        return records
    
    async def get_exercise_history(self, profile_id: str, days: int = 30) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT * FROM exercise_records 
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, start_date))
        
        records = []
        for row in c.fetchall():
            records.append({
                "exercise_type": row['exercise_type'],
                "duration_minutes": row['duration_minutes'],
                "calories": row['calories'],
                "distance_km": row['distance_km'],
                "note": row['note'],
                "recorded_at": row['recorded_at']
            })
        
        return records
    
    async def get_health_report(self, profile_id: str, days: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM health_profiles WHERE profile_id = ?', (profile_id,))
        profile_row = c.fetchone()
        
        if not profile_row:
            return {"error": "Profile not found"}
        
        profile = {
            "id": profile_row['profile_id'],
            "member_name": profile_row['member_name'],
            "gender": profile_row['gender'],
            "birth_date": profile_row['birth_date'],
            "height": profile_row['height'],
            "blood_type": profile_row['blood_type']
        }
        
        weight_records = await self.get_weight_history(profile_id, days)
        bp_records = await self.get_blood_pressure_history(profile_id, days)
        glucose_records = await self.get_blood_glucose_history(profile_id, days)
        exercise_records = await self.get_exercise_history(profile_id, days)
        
        weight_summary = {}
        if weight_records:
            weights = [r['weight'] for r in weight_records]
            weight_summary = {
                "latest": weight_records[0],
                "min": min(weights),
                "max": max(weights),
                "avg": round(sum(weights) / len(weights), 1),
                "count": len(weight_records)
            }
        
        bp_summary = {}
        if bp_records:
            systolics = [r['systolic'] for r in bp_records]
            diastolics = [r['diastolic'] for r in bp_records]
            bp_summary = {
                "latest": bp_records[0],
                "avg_systolic": round(sum(systolics) / len(systolics)),
                "avg_diastolic": round(sum(diastolics) / len(diastolics)),
                "count": len(bp_records)
            }
        
        glucose_summary = {}
        if glucose_records:
            glucoses = [r['glucose'] for r in glucose_records]
            glucose_summary = {
                "latest": glucose_records[0],
                "min": min(glucoses),
                "max": max(glucoses),
                "avg": round(sum(glucoses) / len(glucoses), 1),
                "count": len(glucose_records)
            }
        
        exercise_summary = {}
        if exercise_records:
            total_duration = sum(r['duration_minutes'] for r in exercise_records)
            total_calories = sum(r['calories'] or 0 for r in exercise_records)
            total_distance = sum(r['distance_km'] or 0 for r in exercise_records)
            
            exercise_summary = {
                "total_duration_minutes": total_duration,
                "total_calories": total_calories,
                "total_distance_km": round(total_distance, 1),
                "count": len(exercise_records),
                "types": list(set(r['exercise_type'] for r in exercise_records))
            }
        
        return {
            "profile": profile,
            "period_days": days,
            "weight": weight_summary,
            "blood_pressure": bp_summary,
            "blood_glucose": glucose_summary,
            "exercise": exercise_summary,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_exercise_stats(self, profile_id: str = None, days: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        if profile_id:
            c.execute('''
                SELECT 
                    SUM(duration_minutes) as total_duration,
                    SUM(calories) as total_calories,
                    SUM(distance_km) as total_distance,
                    COUNT(*) as count
                FROM exercise_records 
                WHERE profile_id = ? AND recorded_at >= ?
            ''', (profile_id, start_date))
        else:
            c.execute('''
                SELECT 
                    SUM(duration_minutes) as total_duration,
                    SUM(calories) as total_calories,
                    SUM(distance_km) as total_distance,
                    COUNT(*) as count
                FROM exercise_records 
                WHERE recorded_at >= ?
            ''', (start_date,))
        
        row = c.fetchone()
        
        return {
            "total_duration_minutes": row['total_duration'] or 0,
            "total_calories": row['total_calories'] or 0,
            "total_distance_km": round(row['total_distance'] or 0, 1),
            "exercise_count": row['count'] or 0,
            "period_days": days
        }
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[HealthService] = None


def get_service() -> HealthService:
    global _service_instance
    if _service_instance is None:
        _service_instance = HealthService()
    return _service_instance


async def create_profile(member_name: str, **kwargs) -> Dict[str, Any]:
    return await get_service().create_profile(member_name, **kwargs)


async def record_weight(profile_id: str, weight: float, note: str = None) -> Dict[str, Any]:
    return await get_service().record_weight(profile_id, weight, note)


async def record_blood_pressure(profile_id: str, systolic: int, diastolic: int, **kwargs) -> Dict[str, Any]:
    return await get_service().record_blood_pressure(profile_id, systolic, diastolic, **kwargs)


async def record_blood_glucose(profile_id: str, glucose: float, **kwargs) -> Dict[str, Any]:
    return await get_service().record_blood_glucose(profile_id, glucose, **kwargs)


async def record_exercise(profile_id: str, exercise_type: str, duration_minutes: int, **kwargs) -> Dict[str, Any]:
    return await get_service().record_exercise(profile_id, exercise_type, duration_minutes, **kwargs)


async def get_history(profile_id: str, record_type: str, days: int = 30) -> List[Dict[str, Any]]:
    service = get_service()
    if record_type == "weight":
        return await service.get_weight_history(profile_id, days)
    elif record_type == "blood_pressure":
        return await service.get_blood_pressure_history(profile_id, days)
    elif record_type == "blood_glucose":
        return await service.get_blood_glucose_history(profile_id, days)
    elif record_type == "exercise":
        return await service.get_exercise_history(profile_id, days)
    return []


async def generate_report(profile_id: str, days: int = 7) -> Dict[str, Any]:
    return await get_service().get_health_report(profile_id, days)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = HealthService(':memory:')
        
        print("=== 健康档案服务测试 ===\n")
        
        print("1. 创建健康档案...")
        profile = await service.create_profile(
            member_name="张三",
            gender="male",
            birth_date="1990-05-15",
            height=175.0,
            blood_type="A"
        )
        print(f"   创建档案: {profile}")
        profile_id = profile['id']
        
        print("\n2. 列出所有档案...")
        profiles = await service.list_profiles()
        print(f"   共 {len(profiles)} 个档案")
        for p in profiles:
            print(f"   - {p['member_name']} ({p['gender']}, {p['height']}cm)")
        
        print("\n3. 记录体重...")
        weight = await service.record_weight(profile_id, 70.5, "晨起空腹")
        print(f"   体重记录: {weight}")
        
        weight2 = await service.record_weight(profile_id, 71.0, "晚餐后")
        print(f"   体重记录: {weight2}")
        
        print("\n4. 记录血压...")
        bp = await service.record_blood_pressure(profile_id, 120, 80, pulse=72, note="晨起")
        print(f"   血压记录: {bp}")
        
        print("\n5. 记录血糖...")
        glucose = await service.record_blood_glucose(profile_id, 5.6, "fasting", "空腹血糖")
        print(f"   血糖记录: {glucose}")
        
        print("\n6. 记录运动...")
        exercise = await service.record_exercise(profile_id, "跑步", 30, calories=300, distance_km=5.0)
        print(f"   运动记录: {exercise}")
        
        exercise2 = await service.record_exercise(profile_id, "游泳", 45, calories=400)
        print(f"   运动记录: {exercise2}")
        
        print("\n7. 查询历史记录...")
        weight_history = await service.get_weight_history(profile_id, days=30)
        print(f"   体重历史: {len(weight_history)} 条记录")
        
        print("\n8. 获取健康报告...")
        report = await service.get_health_report(profile_id, days=7)
        print(f"   档案: {report['profile']['member_name']}")
        print(f"   体重统计: {report['weight']}")
        print(f"   血压统计: {report['blood_pressure']}")
        print(f"   血糖统计: {report['blood_glucose']}")
        print(f"   运动统计: {report['exercise']}")
        
        print("\n9. 获取运动统计...")
        stats = await service.get_exercise_stats(profile_id, days=7)
        print(f"   {stats}")
        
        print("\n10. 更新档案...")
        updated = await service.update_profile(profile_id, height=176.0)
        print(f"   更新后: {updated}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())