#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人数据服务 - 管理用户手机采集的数据
"""

import sqlite3
import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


class PersonalDataService:
    """个人数据管理服务"""
    
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
        
        # 位置记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS location_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL DEFAULT 10.0,
                place_type TEXT DEFAULT 'other',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 已知地点表
        c.execute('''
            CREATE TABLE IF NOT EXISTS known_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                place_type TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                radius INTEGER DEFAULT 100
            )
        ''')
        
        # 健康数据表
        c.execute('''
            CREATE TABLE IF NOT EXISTS personal_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                steps INTEGER,
                heart_rate INTEGER,
                sleep_hours REAL,
                calories INTEGER,
                active_minutes INTEGER,
                date DATE NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 消费记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS personal_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                merchant TEXT,
                category TEXT,
                payment_type TEXT DEFAULT 'expense',
                platform TEXT,
                source TEXT DEFAULT 'mobile_sync',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_location_time ON location_records(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_health_date ON personal_health(date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_time ON personal_payments(timestamp)')
        
        self._conn.commit()
    
    # ========== 位置数据 ==========
    
    def record_location(self, latitude: float, longitude: float, 
                       accuracy: float = 10.0) -> Dict[str, Any]:
        """记录位置数据"""
        c = self._get_conn().cursor()
        
        # 检测地点类型
        place_type = self._detect_place(latitude, longitude)
        
        c.execute('''
            INSERT INTO location_records (latitude, longitude, accuracy, place_type)
            VALUES (?, ?, ?, ?)
        ''', (latitude, longitude, accuracy, place_type))
        
        self._conn.commit()
        
        # 检查是否触发自动化
        automations = self._check_location_automations(place_type)
        
        return {
            'success': True,
            'place_type': place_type,
            'automations': automations
        }
    
    def _detect_place(self, lat: float, lng: float) -> str:
        """检测位置类型"""
        c = self._get_conn().cursor()
        
        c.execute('SELECT name, place_type, latitude, longitude, radius FROM known_places')
        
        for row in c.fetchall():
            distance = self._calculate_distance(lat, lng, row['latitude'], row['longitude'])
            if distance <= row['radius']:
                return row['place_type']
        
        return 'other'
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点距离（米）"""
        R = 6371000
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _check_location_automations(self, place_type: str) -> List[str]:
        """检查位置触发自动化"""
        automations = []
        
        if place_type == 'home':
            automations.append('已到家，开启回家模式')
        elif place_type == 'work':
            automations.append('已到公司，开启工作模式')
        
        return automations
    
    def add_known_place(self, name: str, place_type: str, 
                       latitude: float, longitude: float, radius: int = 100) -> Dict[str, Any]:
        """添加已知地点"""
        c = self._get_conn().cursor()
        
        c.execute('''
            INSERT INTO known_places (name, place_type, latitude, longitude, radius)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, place_type, latitude, longitude, radius))
        
        self._conn.commit()
        
        return {'success': True, 'place_id': c.lastrowid}
    
    def get_location_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取位置历史"""
        c = self._get_conn().cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        c.execute('''
            SELECT * FROM location_records 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        ''', (since.isoformat(),))
        
        return [dict(row) for row in c.fetchall()]
    
    def get_location_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取位置统计"""
        c = self._get_conn().cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT place_type, COUNT(*) as count
            FROM location_records
            WHERE timestamp >= ?
            GROUP BY place_type
        ''', (since.isoformat(),))
        
        stats = {row['place_type']: row['count'] for row in c.fetchall()}
        
        return {
            'home_count': stats.get('home', 0),
            'work_count': stats.get('work', 0),
            'other_count': stats.get('other', 0),
            'period_days': days
        }
    
    # ========== 健康数据 ==========
    
    def record_health(self, steps: int = None, heart_rate: int = None,
                     sleep_hours: float = None, calories: int = None) -> Dict[str, Any]:
        """记录健康数据"""
        c = self._get_conn().cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查今天是否已有记录
        c.execute('SELECT id FROM personal_health WHERE date = ?', (today,))
        existing = c.fetchone()
        
        if existing:
            # 更新
            updates = []
            values = []
            
            if steps is not None:
                updates.append('steps = ?')
                values.append(steps)
            if heart_rate is not None:
                updates.append('heart_rate = ?')
                values.append(heart_rate)
            if sleep_hours is not None:
                updates.append('sleep_hours = ?')
                values.append(sleep_hours)
            if calories is not None:
                updates.append('calories = ?')
                values.append(calories)
            
            if updates:
                values.append(today)
                c.execute(f'''
                    UPDATE personal_health 
                    SET {', '.join(updates)}
                    WHERE date = ?
                ''', values)
        else:
            # 新增
            c.execute('''
                INSERT INTO personal_health (steps, heart_rate, sleep_hours, calories, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (steps, heart_rate, sleep_hours, calories, today))
        
        self._conn.commit()
        
        # 生成健康建议
        advice = self._generate_health_advice(steps, heart_rate, sleep_hours)
        
        return {
            'success': True,
            'advice': advice
        }
    
    def _generate_health_advice(self, steps: int, heart_rate: int, sleep_hours: float) -> str:
        """生成健康建议"""
        advice = []
        
        if steps is not None and steps < 5000:
            advice.append('今日步数偏少，建议多走动')
        elif steps is not None and steps >= 10000:
            advice.append('步数达标，继续保持')
        
        if heart_rate is not None and heart_rate > 100:
            advice.append('心率偏高，建议休息')
        
        if sleep_hours is not None and sleep_hours < 7:
            advice.append('睡眠不足，建议早点休息')
        
        return '；'.join(advice) if advice else '健康状况良好'
    
    def get_health_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取健康历史"""
        c = self._get_conn().cursor()
        
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT * FROM personal_health
            WHERE date >= ?
            ORDER BY date DESC
        ''', (since,))
        
        return [dict(row) for row in c.fetchall()]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        c = self._get_conn().cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        c.execute('SELECT * FROM personal_health WHERE date = ?', (today,))
        today_data = c.fetchone()
        
        # 本周统计
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT 
                SUM(steps) as total_steps,
                AVG(heart_rate) as avg_heart_rate,
                AVG(sleep_hours) as avg_sleep,
                SUM(calories) as total_calories
            FROM personal_health
            WHERE date >= ?
        ''', (week_start,))
        
        week_stats = c.fetchone()
        
        return {
            'today': dict(today_data) if today_data else None,
            'week': {
                'total_steps': week_stats['total_steps'] or 0,
                'avg_heart_rate': round(week_stats['avg_heart_rate'] or 0),
                'avg_sleep': round(week_stats['avg_sleep'] or 0, 1),
                'total_calories': week_stats['total_calories'] or 0
            }
        }
    
    # ========== 支付数据 ==========
    
    def record_payment(self, amount: float, merchant: str, category: str = None,
                      payment_type: str = 'expense', platform: str = None) -> Dict[str, Any]:
        """记录支付（自动记账）"""
        c = self._get_conn().cursor()
        
        # 自动分类
        if not category:
            category = self._auto_categorize(merchant)
        
        c.execute('''
            INSERT INTO personal_payments (amount, merchant, category, payment_type, platform)
            VALUES (?, ?, ?, ?, ?)
        ''', (amount, merchant, category, payment_type, platform))
        
        self._conn.commit()
        
        # 检查预算
        budget_warning = self._check_budget(amount, category)
        
        return {
            'success': True,
            'category': category,
            'budget_warning': budget_warning
        }
    
    def _auto_categorize(self, merchant: str) -> str:
        """自动分类"""
        merchant_lower = merchant.lower()
        
        categories = {
            '餐饮': ['美团', '饿了么', '外卖', '餐厅', '肯德基', '麦当劳', '星巴克', '奶茶'],
            '交通': ['滴滴', '打车', '地铁', '公交', '加油', '停车'],
            '购物': ['淘宝', '京东', '拼多多', '超市', '便利店'],
            '娱乐': ['电影', '游戏', '音乐', '视频'],
            '通讯': ['移动', '联通', '电信', '话费'],
            '水电': ['水费', '电费', '燃气'],
        }
        
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw.lower() in merchant_lower:
                    return cat
        
        return '其他'
    
    def _check_budget(self, amount: float, category: str) -> str:
        """检查预算"""
        c = self._get_conn().cursor()
        
        # 获取本月该分类支出
        month_start = datetime.now().strftime('%Y-%m-01')
        
        c.execute('''
            SELECT SUM(amount) as total
            FROM personal_payments
            WHERE category = ? AND payment_type = 'expense'
            AND timestamp >= ?
        ''', (category, month_start))
        
        total = c.fetchone()['total'] or 0
        
        # 简单预算检查
        budgets = {
            '餐饮': 2000,
            '交通': 500,
            '购物': 1000,
            '娱乐': 500,
        }
        
        budget = budgets.get(category, 0)
        if budget > 0 and total + amount > budget:
            return f'{category}本月预算已超 ({total + amount}/{budget}元)'
        
        return None
    
    def get_payment_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取支付历史"""
        c = self._get_conn().cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        c.execute('''
            SELECT * FROM personal_payments
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))
        
        return [dict(row) for row in c.fetchall()]
    
    def get_payment_summary(self, month: str = None) -> Dict[str, Any]:
        """获取支付摘要"""
        c = self._get_conn().cursor()
        
        if not month:
            month = datetime.now().strftime('%Y-%m')
        
        month_start = f'{month}-01'
        
        c.execute('''
            SELECT 
                payment_type,
                SUM(amount) as total,
                COUNT(*) as count
            FROM personal_payments
            WHERE timestamp >= ?
            GROUP BY payment_type
        ''', (month_start,))
        
        by_type = {row['payment_type']: {'total': row['total'], 'count': row['count']} 
                   for row in c.fetchall()}
        
        c.execute('''
            SELECT category, SUM(amount) as total
            FROM personal_payments
            WHERE timestamp >= ? AND payment_type = 'expense'
            GROUP BY category
            ORDER BY total DESC
        ''', (month_start,))
        
        by_category = {row['category']: row['total'] for row in c.fetchall()}
        
        return {
            'month': month,
            'total_expense': by_type.get('expense', {}).get('total', 0),
            'total_income': by_type.get('income', {}).get('total', 0),
            'transaction_count': sum(t['count'] for t in by_type.values()),
            'by_category': by_category
        }


# 全局实例
_service_instance = None

def get_service() -> PersonalDataService:
    global _service_instance
    if _service_instance is None:
        _service_instance = PersonalDataService()
    return _service_instance