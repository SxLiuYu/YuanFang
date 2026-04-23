#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测服务
检测健康异常、消费异常、位置异常
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class AnomalyLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyType(Enum):
    HEALTH_HEART_RATE_HIGH = "health_heart_rate_high"
    HEALTH_HEART_RATE_LOW = "health_heart_rate_low"
    HEALTH_BLOOD_PRESSURE_HIGH = "health_blood_pressure_high"
    HEALTH_BLOOD_PRESSURE_LOW = "health_blood_pressure_low"
    HEALTH_BLOOD_GLUCOSE_HIGH = "health_blood_glucose_high"
    HEALTH_BLOOD_GLUCOSE_LOW = "health_blood_glucose_low"
    HEALTH_SLEEP_ABNORMAL = "health_sleep_abnormal"
    HEALTH_WEIGHT_CHANGE = "health_weight_change"
    
    EXPENSE_OVER_BUDGET = "expense_over_budget"
    EXPENSE_UNUSUAL_AMOUNT = "expense_unusual_amount"
    EXPENSE_SUSPICIOUS = "expense_suspicious"
    EXPENSE_FREQUENCY_ABNORMAL = "expense_frequency_abnormal"
    
    LOCATION_UNUSUAL_TIME = "location_unusual_time"
    LOCATION_UNUSUAL_PLACE = "location_unusual_place"
    LOCATION_PATTERN_BREAK = "location_pattern_break"


@dataclass
class Anomaly:
    anomaly_id: str
    anomaly_type: AnomalyType
    level: AnomalyLevel
    title: str
    description: str
    value: Any
    threshold: Any
    detected_at: datetime
    profile_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnomalyDetectionService:
    """异常检测服务"""
    
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
            CREATE TABLE IF NOT EXISTS anomaly_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_id TEXT UNIQUE,
                profile_id TEXT,
                anomaly_type TEXT NOT NULL,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                value TEXT,
                threshold TEXT,
                metadata TEXT,
                is_resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP,
                detected_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                anomaly_type TEXT NOT NULL,
                threshold_min REAL,
                threshold_max REAL,
                custom_settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(profile_id, anomaly_type)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS location_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                latitude REAL,
                longitude REAL,
                location_name TEXT,
                location_type TEXT,
                is_unusual INTEGER DEFAULT 0,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_profile ON anomaly_records(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_type ON anomaly_records(anomaly_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_detected ON anomaly_records(detected_at)')
        try:
            c.execute('CREATE INDEX IF NOT EXISTS idx_location_profile ON location_records(profile_id)')
        except:
            pass
        self._conn.commit()
        logger.info("Anomaly detection service database initialized")
    
    def _generate_anomaly_id(self) -> str:
        import uuid
        return f"anomaly_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    async def detect_health_anomalies(self, profile_id: str, days: int = 7) -> List[Anomaly]:
        """检测健康异常"""
        anomalies = []
        
        anomalies.extend(await self._detect_heart_rate_anomalies(profile_id, days))
        anomalies.extend(await self._detect_blood_pressure_anomalies(profile_id, days))
        anomalies.extend(await self._detect_blood_glucose_anomalies(profile_id, days))
        anomalies.extend(await self._detect_sleep_anomalies(profile_id, days))
        anomalies.extend(await self._detect_weight_anomalies(profile_id, days))
        
        for anomaly in anomalies:
            await self._save_anomaly(anomaly)
        
        return anomalies
    
    async def _detect_heart_rate_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测心率异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM heart_rate_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if not records:
            return anomalies
        
        thresholds = await self._get_thresholds(profile_id, 'heart_rate')
        min_hr = thresholds.get('min', 50)
        max_hr = thresholds.get('max', 120)
        
        for record in records:
            hr = record.get('heart_rate')
            if hr is None:
                continue
            
            if hr > max_hr:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.HEALTH_HEART_RATE_HIGH,
                    level=AnomalyLevel.WARNING if hr < max_hr * 1.3 else AnomalyLevel.CRITICAL,
                    title="心率过高",
                    description=f"检测到心率 {hr} bpm，超过正常上限 {max_hr} bpm",
                    value=hr,
                    threshold=max_hr,
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"recorded_at": record.get('recorded_at')}
                ))
            elif hr < min_hr:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.HEALTH_HEART_RATE_LOW,
                    level=AnomalyLevel.WARNING if hr > min_hr * 0.7 else AnomalyLevel.CRITICAL,
                    title="心率过低",
                    description=f"检测到心率 {hr} bpm，低于正常下限 {min_hr} bpm",
                    value=hr,
                    threshold=min_hr,
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"recorded_at": record.get('recorded_at')}
                ))
        
        return anomalies
    
    async def _detect_blood_pressure_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测血压异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM blood_pressure_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
            LIMIT 10
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        for record in records:
            systolic = record.get('systolic')
            diastolic = record.get('diastolic')
            
            if systolic is None or diastolic is None:
                continue
            
            if systolic >= 180 or diastolic >= 110:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.HEALTH_BLOOD_PRESSURE_HIGH,
                    level=AnomalyLevel.CRITICAL,
                    title="血压严重偏高",
                    description=f"检测到血压 {systolic}/{diastolic} mmHg，属于高血压3级",
                    value=f"{systolic}/{diastolic}",
                    threshold="140/90",
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"recorded_at": record.get('recorded_at')}
                ))
            elif systolic >= 140 or diastolic >= 90:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.HEALTH_BLOOD_PRESSURE_HIGH,
                    level=AnomalyLevel.WARNING,
                    title="血压偏高",
                    description=f"检测到血压 {systolic}/{diastolic} mmHg，超过正常范围",
                    value=f"{systolic}/{diastolic}",
                    threshold="140/90",
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"recorded_at": record.get('recorded_at')}
                ))
            elif systolic < 90 or diastolic < 60:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.HEALTH_BLOOD_PRESSURE_LOW,
                    level=AnomalyLevel.WARNING,
                    title="血压偏低",
                    description=f"检测到血压 {systolic}/{diastolic} mmHg，低于正常范围",
                    value=f"{systolic}/{diastolic}",
                    threshold="90/60",
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"recorded_at": record.get('recorded_at')}
                ))
        
        return anomalies
    
    async def _detect_blood_glucose_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测血糖异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM blood_glucose_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
            LIMIT 10
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        for record in records:
            glucose = record.get('glucose')
            measure_type = record.get('measure_type', 'fasting')
            
            if glucose is None:
                continue
            
            if measure_type == 'fasting':
                if glucose >= 7.0:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.HEALTH_BLOOD_GLUCOSE_HIGH,
                        level=AnomalyLevel.WARNING if glucose < 11.1 else AnomalyLevel.CRITICAL,
                        title="空腹血糖偏高",
                        description=f"空腹血糖 {glucose} mmol/L，超过正常值",
                        value=glucose,
                        threshold=7.0,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"measure_type": measure_type, "recorded_at": record.get('recorded_at')}
                    ))
                elif glucose < 3.9:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.HEALTH_BLOOD_GLUCOSE_LOW,
                        level=AnomalyLevel.WARNING,
                        title="空腹血糖偏低",
                        description=f"空腹血糖 {glucose} mmol/L，低于正常值",
                        value=glucose,
                        threshold=3.9,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"measure_type": measure_type}
                    ))
            else:
                if glucose >= 11.1:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.HEALTH_BLOOD_GLUCOSE_HIGH,
                        level=AnomalyLevel.WARNING if glucose < 16.7 else AnomalyLevel.CRITICAL,
                        title="餐后血糖偏高",
                        description=f"餐后血糖 {glucose} mmol/L，超过正常值",
                        value=glucose,
                        threshold=11.1,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"measure_type": measure_type}
                    ))
        
        return anomalies
    
    async def _detect_sleep_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测睡眠异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM sleep_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 3:
            return anomalies
        
        sleep_durations = []
        for record in records:
            duration = record.get('duration_minutes')
            if duration:
                sleep_durations.append(duration)
        
        if sleep_durations:
            avg_sleep = statistics.mean(sleep_durations)
            std_sleep = statistics.stdev(sleep_durations) if len(sleep_durations) > 1 else 0
            
            thresholds = await self._get_thresholds(profile_id, 'sleep')
            min_sleep = thresholds.get('min', 360)
            max_sleep = thresholds.get('max', 600)
            
            for i, duration in enumerate(sleep_durations[:5]):
                if duration < min_sleep:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.HEALTH_SLEEP_ABNORMAL,
                        level=AnomalyLevel.WARNING if duration > min_sleep * 0.7 else AnomalyLevel.CRITICAL,
                        title="睡眠时间过短",
                        description=f"睡眠时长 {duration/60:.1f} 小时，低于建议的 {min_sleep/60:.1f} 小时",
                        value=duration,
                        threshold=min_sleep,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"recorded_at": records[i].get('recorded_at')}
                    ))
                elif duration > max_sleep:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.HEALTH_SLEEP_ABNORMAL,
                        level=AnomalyLevel.INFO,
                        title="睡眠时间过长",
                        description=f"睡眠时长 {duration/60:.1f} 小时，超过建议的 {max_sleep/60:.1f} 小时",
                        value=duration,
                        threshold=max_sleep,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"recorded_at": records[i].get('recorded_at')}
                    ))
        
        return anomalies
    
    async def _detect_weight_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测体重异常变化"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM weight_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 3:
            return anomalies
        
        weights = [r.get('weight') for r in records if r.get('weight')]
        if len(weights) < 3:
            return anomalies
        
        recent_avg = statistics.mean(weights[:3])
        older_avg = statistics.mean(weights[3:7]) if len(weights) >= 7 else statistics.mean(weights[3:])
        
        change_percent = abs(recent_avg - older_avg) / older_avg * 100
        
        thresholds = await self._get_thresholds(profile_id, 'weight_change')
        max_change = thresholds.get('max', 5)
        
        if change_percent > max_change:
            direction = "增加" if recent_avg > older_avg else "减少"
            anomalies.append(Anomaly(
                anomaly_id=self._generate_anomaly_id(),
                anomaly_type=AnomalyType.HEALTH_WEIGHT_CHANGE,
                level=AnomalyLevel.WARNING if change_percent < max_change * 1.5 else AnomalyLevel.CRITICAL,
                title=f"体重{direction}异常",
                description=f"近期体重{direction} {change_percent:.1f}%，超过正常范围",
                value=recent_avg,
                threshold=older_avg,
                detected_at=datetime.now(),
                profile_id=profile_id,
                metadata={"change_percent": change_percent, "direction": direction}
            ))
        
        return anomalies
    
    async def detect_expense_anomalies(self, profile_id: str = None, days: int = 30) -> List[Anomaly]:
        """检测消费异常"""
        anomalies = []
        
        anomalies.extend(await self._detect_budget_anomalies(profile_id, days))
        anomalies.extend(await self._detect_unusual_expenses(profile_id, days))
        anomalies.extend(await self._detect_suspicious_transactions(profile_id, days))
        anomalies.extend(await self._detect_frequency_anomalies(profile_id, days))
        
        for anomaly in anomalies:
            await self._save_anomaly(anomaly)
        
        return anomalies
    
    async def _detect_budget_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测预算超支"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
        
        c.execute('''
            SELECT category, amount as budget
            FROM budgets
            WHERE month = ?
        ''', (current_month,))
        
        budgets = [dict(row) for row in c.fetchall()]
        
        for budget in budgets:
            category = budget['category']
            budget_amount = budget['budget']
            
            c.execute('''
                SELECT SUM(amount) as spent
                FROM transactions
                WHERE type = 'expense' AND category = ? AND date LIKE ?
            ''', (category, f"{current_month}%"))
            
            result = c.fetchone()
            spent = result['spent'] if result and result['spent'] else 0
            
            if spent > budget_amount:
                over_percent = (spent - budget_amount) / budget_amount * 100
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.EXPENSE_OVER_BUDGET,
                    level=AnomalyLevel.WARNING if over_percent < 30 else AnomalyLevel.CRITICAL,
                    title=f"{category}预算超支",
                    description=f"{category}已支出 {spent:.0f}元，超出预算 {over_percent:.1f}%",
                    value=spent,
                    threshold=budget_amount,
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"category": category, "over_percent": over_percent}
                ))
        
        return anomalies
    
    async def _detect_unusual_expenses(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测异常金额消费"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT category, AVG(amount) as avg_amount, COUNT(*) as count
            FROM transactions
            WHERE type = 'expense' AND date >= ?
            GROUP BY category
            HAVING count >= 5
        ''', (start_date.isoformat(),))
        
        category_stats = {row['category']: {'avg': row['avg_amount'], 'count': row['count']} 
                          for row in c.fetchall()}
        
        c.execute('''
            SELECT * FROM transactions
            WHERE type = 'expense' AND date >= ?
            ORDER BY date DESC
        ''', (start_date.isoformat(),))
        
        transactions = [dict(row) for row in c.fetchall()]
        
        for tx in transactions:
            category = tx['category']
            amount = tx['amount']
            
            if category in category_stats:
                avg = category_stats[category]['avg']
                if amount > avg * 3 and amount > 100:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.EXPENSE_UNUSUAL_AMOUNT,
                        level=AnomalyLevel.WARNING,
                        title=f"{category}异常消费",
                        description=f"检测到 {category} 类别有一笔 {amount:.0f}元 的消费，远超平均 {avg:.0f}元",
                        value=amount,
                        threshold=avg * 3,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"category": category, "transaction_id": tx.get('id'), "avg": avg}
                    ))
        
        return anomalies
    
    async def _detect_suspicious_transactions(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测可疑交易"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        suspicious_keywords = ['博彩', '赌博', '投资理财', '贷款', '借贷', '信用卡套现']
        
        c.execute('''
            SELECT * FROM transactions
            WHERE date >= ?
            ORDER BY date DESC
        ''', (start_date.isoformat(),))
        
        transactions = [dict(row) for row in c.fetchall()]
        
        for tx in transactions:
            description = tx.get('description', '') or ''
            for keyword in suspicious_keywords:
                if keyword in description:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.EXPENSE_SUSPICIOUS,
                        level=AnomalyLevel.CRITICAL,
                        title="检测到可疑交易",
                        description=f"交易描述包含敏感关键词: {keyword}",
                        value=tx['amount'],
                        threshold=0,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"transaction_id": tx.get('id'), "keyword": keyword, "description": description}
                    ))
                    break
        
        late_night_start = 23
        late_night_end = 5
        
        for tx in transactions:
            tx_date = tx.get('date')
            if tx_date:
                try:
                    dt = datetime.fromisoformat(tx_date.replace('Z', '+00:00').replace('+08:00', ''))
                    hour = dt.hour
                    if late_night_end <= hour < late_night_start:
                        amount = tx.get('amount', 0)
                        if amount > 1000:
                            anomalies.append(Anomaly(
                                anomaly_id=self._generate_anomaly_id(),
                                anomaly_type=AnomalyType.EXPENSE_SUSPICIOUS,
                                level=AnomalyLevel.WARNING,
                                title="深夜大额消费",
                                description=f"深夜 {hour}:00 左右检测到 {amount:.0f}元 的消费",
                                value=amount,
                                threshold=1000,
                                detected_at=datetime.now(),
                                profile_id=profile_id,
                                metadata={"transaction_id": tx.get('id'), "hour": hour}
                            ))
                except:
                    pass
        
        return anomalies
    
    async def _detect_frequency_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测消费频率异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT date(date) as tx_date, COUNT(*) as count
            FROM transactions
            WHERE type = 'expense' AND date >= ?
            GROUP BY date(date)
            ORDER BY tx_date DESC
        ''', (start_date.isoformat(),))
        
        daily_counts = [dict(row) for row in c.fetchall()]
        
        if len(daily_counts) >= 7:
            counts = [d['count'] for d in daily_counts]
            avg_count = statistics.mean(counts)
            std_count = statistics.stdev(counts) if len(counts) > 1 else 0
            
            for day in daily_counts[:3]:
                if day['count'] > avg_count + 2 * std_count and day['count'] > avg_count * 2:
                    anomalies.append(Anomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type=AnomalyType.EXPENSE_FREQUENCY_ABNORMAL,
                        level=AnomalyLevel.WARNING,
                        title="消费频率异常",
                        description=f"当日消费次数 {day['count']} 次，远高于日均 {avg_count:.1f} 次",
                        value=day['count'],
                        threshold=avg_count,
                        detected_at=datetime.now(),
                        profile_id=profile_id,
                        metadata={"date": day['tx_date']}
                    ))
        
        return anomalies
    
    async def detect_location_anomalies(self, profile_id: str, days: int = 7) -> List[Anomaly]:
        """检测位置异常"""
        anomalies = []
        
        anomalies.extend(await self._detect_time_location_anomalies(profile_id, days))
        anomalies.extend(await self._detect_place_anomalies(profile_id, days))
        anomalies.extend(await self._detect_pattern_breaks(profile_id, days))
        
        for anomaly in anomalies:
            await self._save_anomaly(anomaly)
        
        return anomalies
    
    async def _detect_time_location_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测异常时段位置"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        unusual_hours = list(range(0, 6)) + list(range(23, 24))
        
        for record in records:
            recorded_at = record.get('recorded_at')
            if recorded_at:
                try:
                    dt = datetime.fromisoformat(recorded_at.replace('Z', '+00:00').replace('+08:00', ''))
                    hour = dt.hour
                    
                    if hour in unusual_hours and record.get('is_unusual', 0) == 0:
                        location_name = record.get('location_name', '未知位置')
                        anomalies.append(Anomaly(
                            anomaly_id=self._generate_anomaly_id(),
                            anomaly_type=AnomalyType.LOCATION_UNUSUAL_TIME,
                            level=AnomalyLevel.INFO,
                            title="异常时段位置记录",
                            description=f"凌晨 {hour}:00 左右检测到位置活动: {location_name}",
                            value=hour,
                            threshold="正常时段",
                            detected_at=datetime.now(),
                            profile_id=profile_id,
                            metadata={"location_name": location_name, "recorded_at": recorded_at}
                        ))
                except:
                    pass
        
        return anomalies
    
    async def _detect_place_anomalies(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测异常地点"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT location_name, location_type, COUNT(*) as count
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY location_name, location_type
            ORDER BY count DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*4)))
        
        frequent_places = {row['location_name']: row['count'] for row in c.fetchall()}
        
        c.execute('''
            SELECT * FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        recent_records = [dict(row) for row in c.fetchall()]
        
        for record in recent_records:
            location_name = record.get('location_name')
            if location_name and location_name not in frequent_places:
                anomalies.append(Anomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type=AnomalyType.LOCATION_UNUSUAL_PLACE,
                    level=AnomalyLevel.INFO,
                    title="检测到新位置",
                    description=f"首次记录到位置: {location_name}",
                    value=location_name,
                    threshold="常去地点",
                    detected_at=datetime.now(),
                    profile_id=profile_id,
                    metadata={"location_name": location_name, "location_type": record.get('location_type')}
                ))
        
        return anomalies
    
    async def _detect_pattern_breaks(self, profile_id: str, days: int) -> List[Anomaly]:
        """检测出行模式异常"""
        anomalies = []
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT strftime('%w', recorded_at) as weekday,
                   strftime('%H', recorded_at) as hour,
                   COUNT(*) as count
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY weekday, hour
        ''', (profile_id, datetime.now() - timedelta(days=days*4)))
        
        patterns = {}
        for row in c.fetchall():
            key = f"{row['weekday']}_{row['hour']}"
            patterns[key] = row['count']
        
        if not patterns:
            return anomalies
        
        c.execute('''
            SELECT * FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY recorded_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        recent = [dict(row) for row in c.fetchall()]
        
        for record in recent:
            recorded_at = record.get('recorded_at')
            if recorded_at:
                try:
                    dt = datetime.fromisoformat(recorded_at.replace('Z', '+00:00').replace('+08:00', ''))
                    weekday = str(dt.weekday() + 1) if dt.weekday() < 6 else '0'
                    hour = str(dt.hour)
                    key = f"{weekday}_{hour}"
                    
                    if key not in patterns:
                        anomalies.append(Anomaly(
                            anomaly_id=self._generate_anomaly_id(),
                            anomaly_type=AnomalyType.LOCATION_PATTERN_BREAK,
                            level=AnomalyLevel.INFO,
                            title="出行模式异常",
                            description=f"在非常规时段检测到位置活动（周{['日','一','二','三','四','五','六'][int(weekday)]} {hour}:00）",
                            value=f"周{weekday} {hour}:00",
                            threshold="常规出行模式",
                            detected_at=datetime.now(),
                            profile_id=profile_id,
                            metadata={"weekday": weekday, "hour": hour, "location": record.get('location_name')}
                        ))
                except:
                    pass
        
        return anomalies
    
    async def _get_thresholds(self, profile_id: str, anomaly_type: str) -> Dict[str, float]:
        """获取个性化阈值"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT threshold_min, threshold_max, custom_settings
            FROM anomaly_thresholds
            WHERE profile_id = ? AND anomaly_type = ?
        ''', (profile_id, anomaly_type))
        
        row = c.fetchone()
        if row:
            import json
            result = {
                'min': row['threshold_min'],
                'max': row['threshold_max']
            }
            if row['custom_settings']:
                try:
                    custom = json.loads(row['custom_settings'])
                    result.update(custom)
                except:
                    pass
            return result
        
        return {}
    
    async def _save_anomaly(self, anomaly: Anomaly):
        """保存异常记录"""
        import json
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO anomaly_records
            (anomaly_id, profile_id, anomaly_type, level, title, description, 
             value, threshold, metadata, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            anomaly.anomaly_id,
            anomaly.profile_id,
            anomaly.anomaly_type.value,
            anomaly.level.value,
            anomaly.title,
            anomaly.description,
            str(anomaly.value),
            str(anomaly.threshold),
            json.dumps(anomaly.metadata) if anomaly.metadata else None,
            anomaly.detected_at
        ))
        
        conn.commit()
        logger.info(f"Anomaly saved: {anomaly.anomaly_type.value} - {anomaly.title}")
    
    async def get_anomalies(self, profile_id: str = None, anomaly_type: str = None,
                           level: str = None, days: int = 30, resolved: bool = None) -> List[Dict[str, Any]]:
        """获取异常记录"""
        conn = self._get_conn()
        c = conn.cursor()
        
        query = "SELECT * FROM anomaly_records WHERE 1=1"
        params = []
        
        if profile_id:
            query += " AND profile_id = ?"
            params.append(profile_id)
        if anomaly_type:
            query += " AND anomaly_type = ?"
            params.append(anomaly_type)
        if level:
            query += " AND level = ?"
            params.append(level)
        if resolved is not None:
            query += " AND is_resolved = ?"
            params.append(1 if resolved else 0)
        
        start_date = datetime.now() - timedelta(days=days)
        query += " AND detected_at >= ?"
        params.append(start_date)
        
        query += " ORDER BY detected_at DESC"
        
        c.execute(query, params)
        
        anomalies = []
        for row in c.fetchall():
            anomaly = dict(row)
            if anomaly.get('metadata'):
                try:
                    import json
                    anomaly['metadata'] = json.loads(anomaly['metadata'])
                except:
                    pass
            anomalies.append(anomaly)
        
        return anomalies
    
    async def resolve_anomaly(self, anomaly_id: str, note: str = None) -> Dict[str, Any]:
        """标记异常为已处理"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE anomaly_records
            SET is_resolved = 1, resolved_at = ?
            WHERE anomaly_id = ?
        ''', (datetime.now(), anomaly_id))
        
        if c.rowcount == 0:
            return {"error": "Anomaly not found"}
        
        conn.commit()
        logger.info(f"Anomaly resolved: {anomaly_id}")
        
        return {"success": True, "anomaly_id": anomaly_id, "resolved_at": datetime.now().isoformat()}
    
    async def set_threshold(self, profile_id: str, anomaly_type: str,
                           threshold_min: float = None, threshold_max: float = None,
                           custom_settings: Dict = None) -> Dict[str, Any]:
        """设置个性化阈值"""
        import json
        conn = self._get_conn()
        c = conn.cursor()
        
        custom_json = json.dumps(custom_settings) if custom_settings else None
        
        c.execute('''
            INSERT OR REPLACE INTO anomaly_thresholds
            (profile_id, anomaly_type, threshold_min, threshold_max, custom_settings)
            VALUES (?, ?, ?, ?, ?)
        ''', (profile_id, anomaly_type, threshold_min, threshold_max, custom_json))
        
        conn.commit()
        
        return {
            "success": True,
            "profile_id": profile_id,
            "anomaly_type": anomaly_type,
            "threshold_min": threshold_min,
            "threshold_max": threshold_max
        }
    
    async def record_location(self, profile_id: str, latitude: float, longitude: float,
                              location_name: str = None, location_type: str = None,
                              is_unusual: bool = False) -> Dict[str, Any]:
        """记录位置信息"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO location_records
            (profile_id, latitude, longitude, location_name, location_type, is_unusual, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (profile_id, latitude, longitude, location_name, location_type, 1 if is_unusual else 0, datetime.now()))
        
        conn.commit()
        
        return {
            "success": True,
            "profile_id": profile_id,
            "location_name": location_name,
            "recorded_at": datetime.now().isoformat()
        }
    
    async def run_all_detections(self, profile_id: str) -> Dict[str, Any]:
        """运行所有异常检测"""
        health_anomalies = await self.detect_health_anomalies(profile_id)
        expense_anomalies = await self.detect_expense_anomalies(profile_id)
        location_anomalies = await self.detect_location_anomalies(profile_id)
        
        all_anomalies = health_anomalies + expense_anomalies + location_anomalies
        
        summary = {
            "total": len(all_anomalies),
            "by_level": {
                "critical": len([a for a in all_anomalies if a.level == AnomalyLevel.CRITICAL]),
                "warning": len([a for a in all_anomalies if a.level == AnomalyLevel.WARNING]),
                "info": len([a for a in all_anomalies if a.level == AnomalyLevel.INFO])
            },
            "by_type": {
                "health": len(health_anomalies),
                "expense": len(expense_anomalies),
                "location": len(location_anomalies)
            },
            "anomalies": [
                {
                    "id": a.anomaly_id,
                    "type": a.anomaly_type.value,
                    "level": a.level.value,
                    "title": a.title,
                    "description": a.description
                }
                for a in all_anomalies
            ]
        }
        
        return summary
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[AnomalyDetectionService] = None


def get_service() -> AnomalyDetectionService:
    global _service_instance
    if _service_instance is None:
        _service_instance = AnomalyDetectionService()
    return _service_instance


async def detect_health_anomalies(profile_id: str, days: int = 7) -> List[Dict[str, Any]]:
    service = get_service()
    anomalies = await service.detect_health_anomalies(profile_id, days)
    return [{"id": a.anomaly_id, "type": a.anomaly_type.value, "level": a.level.value,
             "title": a.title, "description": a.description} for a in anomalies]


async def detect_expense_anomalies(profile_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
    service = get_service()
    anomalies = await service.detect_expense_anomalies(profile_id, days)
    return [{"id": a.anomaly_id, "type": a.anomaly_type.value, "level": a.level.value,
             "title": a.title, "description": a.description} for a in anomalies]


async def detect_location_anomalies(profile_id: str, days: int = 7) -> List[Dict[str, Any]]:
    service = get_service()
    anomalies = await service.detect_location_anomalies(profile_id, days)
    return [{"id": a.anomaly_id, "type": a.anomaly_type.value, "level": a.level.value,
             "title": a.title, "description": a.description} for a in anomalies]


async def get_anomalies(**kwargs) -> List[Dict[str, Any]]:
    return await get_service().get_anomalies(**kwargs)


async def resolve_anomaly(anomaly_id: str, note: str = None) -> Dict[str, Any]:
    return await get_service().resolve_anomaly(anomaly_id, note)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = AnomalyDetectionService(':memory:')
        
        print("=== 异常检测服务测试 ===\n")
        
        print("1. 运行所有检测...")
        summary = await service.run_all_detections("test_profile")
        print(f"   检测到 {summary['total']} 个异常")
        print(f"   按级别: {summary['by_level']}")
        print(f"   按类型: {summary['by_type']}")
        
        print("\n2. 设置个性化阈值...")
        threshold = await service.set_threshold("test_profile", "heart_rate", 
                                                threshold_min=55, threshold_max=110)
        print(f"   阈值设置: {threshold}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())