#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用药提醒服务 - SQLite持久化版本"""
import logging
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MedicationService:
    """用药提醒服务"""
    
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
            CREATE TABLE IF NOT EXISTS medication_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT UNIQUE,
                profile_id TEXT,
                medication_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                reminder_times TEXT,
                start_date TEXT,
                end_date TEXT,
                notes TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS medication_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT,
                taken_at TIMESTAMP,
                dosage_taken TEXT,
                note TEXT
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_med_plan_id ON medication_plans(plan_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_med_plan_profile ON medication_plans(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_med_plan_status ON medication_plans(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_med_record_plan ON medication_records(plan_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_med_record_taken ON medication_records(taken_at)')
        self._conn.commit()
        logger.info("Medication service database initialized")
    
    async def create_plan(self, medication_name: str, profile_id: str = None,
                          dosage: str = None, frequency: str = None,
                          reminder_times: List[str] = None, start_date: str = None,
                          end_date: str = None, notes: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            plan_id = f"med_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            now = datetime.now()
            reminder_times_str = json.dumps(reminder_times, ensure_ascii=False) if reminder_times else None
            
            c.execute('''
                INSERT INTO medication_plans 
                (plan_id, profile_id, medication_name, dosage, frequency, 
                 reminder_times, start_date, end_date, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plan_id, profile_id, medication_name, dosage, frequency,
                  reminder_times_str, start_date, end_date, notes, 'active', now))
            
            conn.commit()
            
            logger.info(f"Medication plan created: {medication_name} (ID: {plan_id})")
            
            return {
                "id": plan_id,
                "profile_id": profile_id,
                "medication_name": medication_name,
                "dosage": dosage,
                "frequency": frequency,
                "reminder_times": reminder_times,
                "start_date": start_date,
                "end_date": end_date,
                "notes": notes,
                "status": "active",
                "created_at": now.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to create medication plan: {e}")
            return {"error": str(e)}
    
    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM medication_plans WHERE plan_id = ?', (plan_id,))
        row = c.fetchone()
        
        if row:
            reminder_times = json.loads(row['reminder_times']) if row['reminder_times'] else None
            return {
                "id": row['plan_id'],
                "profile_id": row['profile_id'],
                "medication_name": row['medication_name'],
                "dosage": row['dosage'],
                "frequency": row['frequency'],
                "reminder_times": reminder_times,
                "start_date": row['start_date'],
                "end_date": row['end_date'],
                "notes": row['notes'],
                "status": row['status'],
                "created_at": row['created_at']
            }
        
        return {"error": "Plan not found"}
    
    async def list_plans(self, profile_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        query = 'SELECT * FROM medication_plans WHERE 1=1'
        params = []
        
        if profile_id:
            query += ' AND profile_id = ?'
            params.append(profile_id)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC'
        
        c.execute(query, params)
        
        plans = []
        for row in c.fetchall():
            reminder_times = json.loads(row['reminder_times']) if row['reminder_times'] else None
            plans.append({
                "id": row['plan_id'],
                "profile_id": row['profile_id'],
                "medication_name": row['medication_name'],
                "dosage": row['dosage'],
                "frequency": row['frequency'],
                "reminder_times": reminder_times,
                "start_date": row['start_date'],
                "end_date": row['end_date'],
                "notes": row['notes'],
                "status": row['status'],
                "created_at": row['created_at']
            })
        
        return plans
    
    async def update_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        allowed_fields = ['medication_name', 'dosage', 'frequency', 'reminder_times',
                          'start_date', 'end_date', 'notes', 'status']
        updates = {}
        
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == 'reminder_times' and isinstance(v, list):
                    updates[k] = json.dumps(v, ensure_ascii=False)
                else:
                    updates[k] = v
        
        if not updates:
            return {"error": "No valid fields to update"}
        
        conn = self._get_conn()
        c = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [plan_id]
        
        c.execute(f"UPDATE medication_plans SET {set_clause} WHERE plan_id = ?", values)
        
        if c.rowcount == 0:
            return {"error": "Plan not found"}
        
        conn.commit()
        logger.info(f"Medication plan updated: {plan_id}")
        
        return await self.get_plan(plan_id)
    
    async def delete_plan(self, plan_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM medication_plans WHERE plan_id = ?', (plan_id,))
        
        if c.rowcount == 0:
            return {"error": "Plan not found"}
        
        c.execute('DELETE FROM medication_records WHERE plan_id = ?', (plan_id,))
        
        conn.commit()
        
        logger.info(f"Medication plan deleted: {plan_id}")
        return {"success": True, "message": f"Plan {plan_id} and all records deleted"}
    
    async def set_reminder_times(self, plan_id: str, reminder_times: List[str]) -> Dict[str, Any]:
        return await self.update_plan(plan_id, reminder_times=reminder_times)
    
    async def record_take(self, plan_id: str, dosage_taken: str = None, note: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM medication_plans WHERE plan_id = ?', (plan_id,))
        if not c.fetchone():
            return {"error": "Plan not found"}
        
        now = datetime.now()
        
        c.execute('''
            INSERT INTO medication_records (plan_id, taken_at, dosage_taken, note)
            VALUES (?, ?, ?, ?)
        ''', (plan_id, now, dosage_taken, note))
        
        conn.commit()
        
        logger.info(f"Medication taken recorded: {plan_id} at {now}")
        
        return {
            "plan_id": plan_id,
            "taken_at": now.isoformat(),
            "dosage_taken": dosage_taken,
            "note": note
        }
    
    async def get_records(self, plan_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        if plan_id:
            c.execute('''
                SELECT * FROM medication_records 
                WHERE plan_id = ? AND taken_at >= ?
                ORDER BY taken_at DESC
            ''', (plan_id, start_date))
        else:
            c.execute('''
                SELECT * FROM medication_records 
                WHERE taken_at >= ?
                ORDER BY taken_at DESC
            ''', (start_date,))
        
        records = []
        for row in c.fetchall():
            records.append({
                "plan_id": row['plan_id'],
                "taken_at": row['taken_at'],
                "dosage_taken": row['dosage_taken'],
                "note": row['note']
            })
        
        return records
    
    async def get_today_medications(self, profile_id: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = '''
            SELECT p.*, 
                   r.taken_at, r.dosage_taken as actual_dosage, r.note as take_note
            FROM medication_plans p
            LEFT JOIN medication_records r ON p.plan_id = r.plan_id 
                AND r.taken_at >= ? AND r.taken_at <= ?
            WHERE p.status = 'active'
        '''
        params = [today_start, today_end]
        
        if profile_id:
            query += ' AND p.profile_id = ?'
            params.append(profile_id)
        
        query += ' ORDER BY p.reminder_times'
        
        c.execute(query, params)
        
        medications = []
        for row in c.fetchall():
            reminder_times = json.loads(row['reminder_times']) if row['reminder_times'] else None
            medications.append({
                "id": row['plan_id'],
                "profile_id": row['profile_id'],
                "medication_name": row['medication_name'],
                "dosage": row['dosage'],
                "frequency": row['frequency'],
                "reminder_times": reminder_times,
                "status": row['status'],
                "taken_today": row['taken_at'] is not None,
                "taken_at": row['taken_at'],
                "actual_dosage": row['actual_dosage'],
                "take_note": row['take_note']
            })
        
        return medications
    
    async def get_reminders(self, profile_id: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        today = now.date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        query = '''
            SELECT p.*, 
                   r.taken_at
            FROM medication_plans p
            LEFT JOIN medication_records r ON p.plan_id = r.plan_id 
                AND r.taken_at >= ? AND r.taken_at <= ?
            WHERE p.status = 'active'
        '''
        params = [today_start, today_end]
        
        if profile_id:
            query += ' AND p.profile_id = ?'
            params.append(profile_id)
        
        c.execute(query, params)
        
        reminders = []
        for row in c.fetchall():
            reminder_times = json.loads(row['reminder_times']) if row['reminder_times'] else []
            taken = row['taken_at'] is not None
            
            next_reminder = None
            if reminder_times and not taken:
                for rt in sorted(reminder_times):
                    if rt > current_time:
                        next_reminder = rt
                        break
            
            reminders.append({
                "id": row['plan_id'],
                "profile_id": row['profile_id'],
                "medication_name": row['medication_name'],
                "dosage": row['dosage'],
                "frequency": row['frequency'],
                "reminder_times": reminder_times,
                "taken": taken,
                "next_reminder": next_reminder,
                "status": "completed" if taken else "pending"
            })
        
        reminders.sort(key=lambda x: (x['taken'], x['next_reminder'] or '99:99'))
        return reminders
    
    async def get_medication_stats(self, profile_id: str = None, days: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        if profile_id:
            c.execute('''
                SELECT COUNT(*) as total_taken
                FROM medication_records r
                JOIN medication_plans p ON r.plan_id = p.plan_id
                WHERE p.profile_id = ? AND r.taken_at >= ?
            ''', (profile_id, start_date))
        else:
            c.execute('''
                SELECT COUNT(*) as total_taken
                FROM medication_records 
                WHERE taken_at >= ?
            ''', (start_date,))
        
        row = c.fetchone()
        
        if profile_id:
            c.execute('''
                SELECT COUNT(*) as total_plans
                FROM medication_plans
                WHERE profile_id = ? AND status = 'active'
            ''', (profile_id,))
        else:
            c.execute('''
                SELECT COUNT(*) as total_plans
                FROM medication_plans
                WHERE status = 'active'
            ''')
        
        plans_row = c.fetchone()
        
        return {
            "total_plans": plans_row['total_plans'] or 0,
            "total_taken": row['total_taken'] or 0,
            "period_days": days
        }
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[MedicationService] = None


def get_service() -> MedicationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MedicationService()
    return _service_instance


async def create_schedule(medication_name: str, **kwargs) -> Dict[str, Any]:
    return await get_service().create_plan(medication_name, **kwargs)


async def get_reminders(profile_id: str = None) -> List[Dict[str, Any]]:
    return await get_service().get_reminders(profile_id)


async def record_take(plan_id: str, dosage_taken: str = None, note: str = None) -> Dict[str, Any]:
    return await get_service().record_take(plan_id, dosage_taken, note)


async def check_inventory() -> Dict[str, Any]:
    stats = await get_service().get_medication_stats()
    return {"inventory": stats}


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = MedicationService(':memory:')
        
        print("=== 用药提醒服务测试 ===\n")
        
        print("1. 创建用药计划...")
        plan1 = await service.create_plan(
            medication_name="阿司匹林",
            profile_id="profile_test",
            dosage="100mg",
            frequency="每日一次",
            reminder_times=["08:00", "20:00"],
            start_date="2025-01-01",
            notes="饭后服用"
        )
        print(f"   创建计划: {plan1}")
        plan_id = plan1['id']
        
        plan2 = await service.create_plan(
            medication_name="维生素D",
            profile_id="profile_test",
            dosage="400IU",
            frequency="每日一次",
            reminder_times=["09:00"],
            start_date="2025-01-01"
        )
        print(f"   创建计划: {plan2}")
        
        print("\n2. 列出所有用药计划...")
        plans = await service.list_plans()
        print(f"   共 {len(plans)} 个计划")
        for p in plans:
            print(f"   - {p['medication_name']} ({p['dosage']}) - {p['frequency']}")
        
        print("\n3. 设置提醒时间...")
        updated = await service.set_reminder_times(plan_id, ["07:00", "19:00"])
        print(f"   更新后提醒时间: {updated.get('reminder_times')}")
        
        print("\n4. 记录用药...")
        record1 = await service.record_take(plan_id, "100mg", "已服用")
        print(f"   用药记录: {record1}")
        
        print("\n5. 查询今日用药...")
        today_meds = await service.get_today_medications()
        print(f"   今日用药: {len(today_meds)} 条")
        for m in today_meds:
            status = "已服用" if m['taken_today'] else "待服用"
            print(f"   - {m['medication_name']}: {status}")
        
        print("\n6. 获取用药提醒...")
        reminders = await service.get_reminders()
        print(f"   提醒列表: {len(reminders)} 条")
        for r in reminders:
            print(f"   - {r['medication_name']}: {r['status']}, 下次提醒: {r.get('next_reminder', '无')}")
        
        print("\n7. 获取用药统计...")
        stats = await service.get_medication_stats()
        print(f"   统计: {stats}")
        
        print("\n8. 查询用药记录...")
        records = await service.get_records()
        print(f"   记录数: {len(records)}")
        for r in records:
            print(f"   - {r['plan_id']}: {r['taken_at']}")
        
        print("\n9. 获取单个计划...")
        plan = await service.get_plan(plan_id)
        print(f"   计划详情: {plan['medication_name']}, 提醒: {plan['reminder_times']}")
        
        print("\n10. 删除计划...")
        delete_result = await service.delete_plan(plan_id)
        print(f"   删除结果: {delete_result}")
        
        remaining_plans = await service.list_plans()
        print(f"   剩余计划数: {len(remaining_plans)}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())