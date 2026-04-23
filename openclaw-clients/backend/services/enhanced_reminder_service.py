#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能提醒服务 - 基于时间/位置/习惯的主动提醒
扩展原有smart_reminder_service，添加数据库持久化
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class EnhancedReminderService:
    """增强智能提醒服务 - 支持持久化和多类型提醒"""
    
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
            CREATE TABLE IF NOT EXISTS enhanced_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id TEXT UNIQUE NOT NULL,
                profile_id TEXT DEFAULT 'default',
                title TEXT NOT NULL,
                description TEXT,
                reminder_type TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                trigger_time TIMESTAMP,
                trigger_location TEXT,
                trigger_condition TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurring_pattern TEXT,
                is_active INTEGER DEFAULT 1,
                is_triggered INTEGER DEFAULT 0,
                triggered_at TIMESTAMP,
                snoozed_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS reminder_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id TEXT NOT NULL,
                notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_taken TEXT
            )
        ''')
        
        self._conn.commit()
    
    # ========== 创建提醒 ==========
    
    def create_reminder(self, title: str, reminder_type: str = 'time',
                       trigger_time: str = None, trigger_location: dict = None,
                       description: str = None, priority: str = 'normal',
                       recurring: str = None, profile_id: str = 'default') -> Dict[str, Any]:
        """通用创建提醒"""
        reminder_id = str(uuid.uuid4())[:8]
        
        c = self._get_conn().cursor()
        c.execute('''
            INSERT INTO enhanced_reminders 
            (reminder_id, profile_id, title, description, reminder_type, priority,
             trigger_time, trigger_location, is_recurring, recurring_pattern)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reminder_id, profile_id, title, description, reminder_type, priority,
              trigger_time, json.dumps(trigger_location) if trigger_location else None,
              1 if recurring else 0, recurring))
        
        self._conn.commit()
        
        return {
            'success': True,
            'reminder_id': reminder_id,
            'message': f'提醒已创建：{title}'
        }
    
    def create_time_reminder(self, title: str, trigger_time: str,
                            description: str = None, priority: str = 'normal',
                            recurring: str = None) -> Dict[str, Any]:
        """创建定时提醒"""
        return self.create_reminder(
            title=title, reminder_type='time', trigger_time=trigger_time,
            description=description, priority=priority, recurring=recurring
        )
    
    def create_location_reminder(self, title: str, latitude: float, longitude: float,
                                radius: int = 100, description: str = None) -> Dict[str, Any]:
        """创建位置提醒"""
        return self.create_reminder(
            title=title, reminder_type='location',
            trigger_location={'latitude': latitude, 'longitude': longitude, 'radius': radius},
            description=description
        )
    
    def create_medication_reminder(self, medication: str, times: List[str],
                                  days: List[str] = None) -> Dict[str, Any]:
        """创建用药提醒"""
        return self.create_reminder(
            title=f'吃{medication}',
            reminder_type='medication',
            description=f'该吃{medication}了',
            trigger_condition={'medication': medication, 'times': times, 'days': days},
            priority='high',
            recurring='daily'
        )
    
    def create_budget_reminder(self, category: str, threshold: float) -> Dict[str, Any]:
        """创建预算提醒"""
        return self.create_reminder(
            title=f'{category}预算提醒',
            reminder_type='budget',
            description=f'{category}消费已超过预算{threshold}元',
            trigger_condition={'category': category, 'threshold': threshold}
        )
    
    # ========== 获取提醒 ==========
    
    def get_reminders(self, profile_id: str = 'default', active_only: bool = True) -> List[Dict]:
        """获取提醒列表"""
        c = self._get_conn().cursor()
        
        if active_only:
            c.execute('''
                SELECT * FROM enhanced_reminders 
                WHERE profile_id = ? AND is_active = 1
                ORDER BY trigger_time ASC
            ''', (profile_id,))
        else:
            c.execute('''
                SELECT * FROM enhanced_reminders 
                WHERE profile_id = ?
                ORDER BY created_at DESC
            ''', (profile_id,))
        
        return [dict(row) for row in c.fetchall()]
    
    def get_pending_reminders(self, profile_id: str = 'default') -> List[Dict]:
        """获取待触发的提醒"""
        c = self._get_conn().cursor()
        now = datetime.now()
        
        c.execute('''
            SELECT * FROM enhanced_reminders 
            WHERE profile_id = ? AND is_active = 1 AND is_triggered = 0
            AND (trigger_time IS NULL OR trigger_time <= ?)
            AND (snoozed_until IS NULL OR snoozed_until <= ?)
            ORDER BY priority DESC, trigger_time ASC
        ''', (profile_id, now.isoformat(), now.isoformat()))
        
        return [dict(row) for row in c.fetchall()]
    
    def get_upcoming(self, hours: int = 24, profile_id: str = 'default') -> List[Dict]:
        """获取即将到来的提醒"""
        c = self._get_conn().cursor()
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        
        c.execute('''
            SELECT * FROM enhanced_reminders 
            WHERE profile_id = ? AND is_active = 1 AND is_triggered = 0
            AND trigger_time BETWEEN ? AND ?
            ORDER BY trigger_time ASC
        ''', (profile_id, now.isoformat(), end_time.isoformat()))
        
        return [dict(row) for row in c.fetchall()]
    
    # ========== 触发提醒 ==========
    
    def trigger(self, reminder_id: str) -> Dict[str, Any]:
        """触发提醒"""
        c = self._get_conn().cursor()
        
        c.execute('SELECT * FROM enhanced_reminders WHERE reminder_id = ?', (reminder_id,))
        reminder = c.fetchone()
        
        if not reminder:
            return {'success': False, 'error': '提醒不存在'}
        
        c.execute('''
            UPDATE enhanced_reminders 
            SET is_triggered = 1, triggered_at = ?
            WHERE reminder_id = ?
        ''', (datetime.now().isoformat(), reminder_id))
        
        c.execute('''
            INSERT INTO reminder_notifications (reminder_id, action_taken)
            VALUES (?, 'triggered')
        ''', (reminder_id,))
        
        self._conn.commit()
        
        return {
            'success': True,
            'reminder': dict(reminder),
            'message': reminder['title']
        }
    
    def check_location_triggers(self, latitude: float, longitude: float,
                                profile_id: str = 'default') -> List[Dict]:
        """检查位置触发"""
        import math
        
        c = self._get_conn().cursor()
        
        c.execute('''
            SELECT * FROM enhanced_reminders 
            WHERE profile_id = ? AND reminder_type = 'location' 
            AND is_active = 1 AND is_triggered = 0
        ''', (profile_id,))
        
        triggered = []
        
        for row in c.fetchall():
            try:
                location = json.loads(row['trigger_location'])
                R = 6371000
                phi1, phi2 = math.radians(latitude), math.radians(location['latitude'])
                dphi = math.radians(location['latitude'] - latitude)
                dlambda = math.radians(location['longitude'] - longitude)
                a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
                distance = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                
                if distance <= location.get('radius', 100):
                    result = self.trigger(row['reminder_id'])
                    if result['success']:
                        triggered.append(result['reminder'])
            except:
                continue
        
        return triggered
    
    # ========== 管理操作 ==========
    
    def snooze(self, reminder_id: str, minutes: int = 10) -> Dict[str, Any]:
        """推迟提醒"""
        c = self._get_conn().cursor()
        
        snoozed_until = datetime.now() + timedelta(minutes=minutes)
        
        c.execute('''
            UPDATE enhanced_reminders 
            SET snoozed_until = ?, is_triggered = 0
            WHERE reminder_id = ?
        ''', (snoozed_until.isoformat(), reminder_id))
        
        self._conn.commit()
        
        return {'success': True, 'message': f'已推迟{minutes}分钟'}
    
    def complete(self, reminder_id: str) -> Dict[str, Any]:
        """完成提醒"""
        c = self._get_conn().cursor()
        
        c.execute('''
            UPDATE enhanced_reminders 
            SET is_active = 0, is_triggered = 1, triggered_at = ?
            WHERE reminder_id = ?
        ''', (datetime.now().isoformat(), reminder_id))
        
        self._conn.commit()
        
        return {'success': True, 'message': '提醒已完成'}
    
    def delete(self, reminder_id: str) -> Dict[str, Any]:
        """删除提醒"""
        c = self._get_conn().cursor()
        
        c.execute('DELETE FROM enhanced_reminders WHERE reminder_id = ?', (reminder_id,))
        self._conn.commit()
        
        return {'success': True, 'message': '提醒已删除'}
    
    # ========== 智能建议 ==========
    
    def get_suggestions(self, profile_id: str = 'default') -> List[Dict]:
        """生成提醒建议"""
        suggestions = []
        
        c = self._get_conn().cursor()
        
        # 检查是否需要运动提醒
        c.execute('''
            SELECT AVG(steps) as avg_steps FROM personal_health 
            WHERE date >= date('now', '-7 days')
        ''')
        health = c.fetchone()
        if health and health['avg_steps'] and health['avg_steps'] < 5000:
            suggestions.append({
                'type': 'habit',
                'title': '增加运动',
                'description': '您最近日均步数较低，建议设置运动提醒'
            })
        
        # 检查用药提醒
        c.execute('''
            SELECT COUNT(*) as count FROM enhanced_reminders 
            WHERE reminder_type = 'medication' AND is_active = 1
        ''')
        if c.fetchone()['count'] == 0:
            suggestions.append({
                'type': 'medication',
                'title': '添加用药提醒',
                'description': '您还没有设置任何用药提醒'
            })
        
        return suggestions


# 全局实例
_enhanced_service = None

def get_enhanced_service() -> EnhancedReminderService:
    global _enhanced_service
    if _enhanced_service is None:
        _enhanced_service = EnhancedReminderService()
    return _enhanced_service