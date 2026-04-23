#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级分析报告服务
健康评分、消费洞察、行为分析、AI报告生成
"""
import logging
import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class ScoreLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class ReportType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class InsightCategory(Enum):
    HEALTH = "health"
    SPENDING = "spending"
    BEHAVIOR = "behavior"
    PRODUCTIVITY = "productivity"


@dataclass
class HealthScore:
    overall_score: float
    level: ScoreLevel
    dimensions: Dict[str, float]
    recommendations: List[str]
    trends: Dict[str, str]
    generated_at: datetime


@dataclass
class SpendingInsight:
    category: str
    total_amount: float
    average_amount: float
    trend: str
    anomaly_detected: bool
    savings_potential: float
    recommendations: List[str]


@dataclass
class BehaviorPattern:
    pattern_type: str
    pattern_name: str
    frequency: int
    typical_time: str
    efficiency_score: float
    suggestions: List[str]


@dataclass
class AnalysisReport:
    report_id: str
    report_type: ReportType
    profile_id: str
    period_start: datetime
    period_end: datetime
    health_score: Optional[HealthScore]
    spending_insights: List[SpendingInsight]
    behavior_patterns: List[BehaviorPattern]
    goals_progress: Dict[str, Any]
    personalized_suggestions: List[str]
    generated_at: datetime


class AdvancedAnalyticsService:
    """高级分析报告服务"""
    
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
            CREATE TABLE IF NOT EXISTS analytics_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                profile_id TEXT,
                report_type TEXT NOT NULL,
                period_start TIMESTAMP,
                period_end TIMESTAMP,
                health_score TEXT,
                spending_insights TEXT,
                behavior_patterns TEXT,
                goals_progress TEXT,
                personalized_suggestions TEXT,
                generated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_scores_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                overall_score REAL,
                dimensions TEXT,
                level TEXT,
                generated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                goal_type TEXT NOT NULL,
                goal_name TEXT NOT NULL,
                target_value REAL,
                current_value REAL,
                unit TEXT,
                deadline DATE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(profile_id, goal_type, goal_name)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS behavior_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                behavior_type TEXT NOT NULL,
                behavior_name TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                metadata TEXT,
                recorded_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS analysis_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                insight_type TEXT NOT NULL,
                insight_category TEXT,
                title TEXT,
                description TEXT,
                importance REAL,
                action_required INTEGER DEFAULT 0,
                is_dismissed INTEGER DEFAULT 0,
                valid_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reports_profile ON analytics_reports(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_scores_profile ON health_scores_history(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_goals_profile ON user_goals(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_behavior_profile ON behavior_records(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_insights_profile ON analysis_insights(profile_id)')
        self._conn.commit()
        logger.info("Advanced analytics service database initialized")
    
    def _generate_report_id(self) -> str:
        import uuid
        return f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _score_to_level(self, score: float) -> ScoreLevel:
        if score >= 90:
            return ScoreLevel.EXCELLENT
        elif score >= 75:
            return ScoreLevel.GOOD
        elif score >= 60:
            return ScoreLevel.FAIR
        elif score >= 40:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.CRITICAL
    
    async def calculate_health_score(self, profile_id: str, days: int = 30) -> HealthScore:
        conn = self._get_conn()
        c = conn.cursor()
        
        dimensions = {}
        recommendations = []
        trends = {}
        
        dimensions['physical_activity'] = await self._calculate_activity_score(c, profile_id, days)
        dimensions['sleep_quality'] = await self._calculate_sleep_score(c, profile_id, days)
        dimensions['heart_health'] = await self._calculate_heart_score(c, profile_id, days)
        dimensions['blood_pressure'] = await self._calculate_bp_score(c, profile_id, days)
        dimensions['blood_glucose'] = await self._calculate_glucose_score(c, profile_id, days)
        dimensions['weight_management'] = await self._calculate_weight_score(c, profile_id, days)
        dimensions['mental_wellness'] = await self._calculate_mental_score(c, profile_id, days)
        
        valid_scores = [s for s in dimensions.values() if s > 0]
        if valid_scores:
            overall_score = statistics.mean(valid_scores)
        else:
            overall_score = 50.0
        
        level = self._score_to_level(overall_score)
        
        if dimensions['physical_activity'] < 60:
            recommendations.append("建议每天进行至少30分钟中等强度运动")
            trends['physical_activity'] = "需改善"
        if dimensions['sleep_quality'] < 60:
            recommendations.append("建议保持规律作息，每晚睡眠7-8小时")
            trends['sleep_quality'] = "需改善"
        if dimensions['heart_health'] < 60:
            recommendations.append("建议关注心率变化，必要时咨询医生")
        if dimensions['blood_pressure'] < 60:
            recommendations.append("血压指标需关注，建议定期监测")
        if dimensions['blood_glucose'] < 60:
            recommendations.append("血糖控制需加强，注意饮食管理")
        if dimensions['weight_management'] < 60:
            recommendations.append("建议保持健康体重，合理饮食运动")
        
        if overall_score >= 75 and not recommendations:
            recommendations.append("继续保持健康的生活方式")
        
        health_score = HealthScore(
            overall_score=round(overall_score, 1),
            level=level,
            dimensions=dimensions,
            recommendations=recommendations,
            trends=trends,
            generated_at=datetime.now()
        )
        
        await self._save_health_score(profile_id, health_score)
        
        return health_score
    
    async def _calculate_activity_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT SUM(steps) as total_steps, COUNT(DISTINCT date(recorded_at)) as active_days
            FROM exercise_records
            WHERE profile_id = ? AND recorded_at >= ?
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        if not row or row['total_steps'] is None:
            return 0.0
        
        total_steps = row['total_steps'] or 0
        active_days = row['active_days'] or 0
        
        avg_daily_steps = total_steps / days if days > 0 else 0
        
        steps_score = min(100, (avg_daily_steps / 10000) * 100)
        consistency_score = min(100, (active_days / days) * 100)
        
        return (steps_score * 0.7 + consistency_score * 0.3)
    
    async def _calculate_sleep_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT AVG(duration_minutes) as avg_duration,
                   AVG(sleep_quality) as avg_quality,
                   COUNT(*) as record_count
            FROM sleep_records
            WHERE profile_id = ? AND recorded_at >= ?
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        if not row or row['avg_duration'] is None:
            return 0.0
        
        avg_duration = row['avg_duration'] or 0
        avg_quality = row['avg_quality'] or 0
        
        optimal_duration = 480
        duration_score = 100 - abs(avg_duration - optimal_duration) / optimal_duration * 50
        duration_score = max(0, min(100, duration_score))
        
        quality_score = avg_quality if avg_quality > 0 else 70
        
        return duration_score * 0.5 + quality_score * 0.5
    
    async def _calculate_heart_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT AVG(heart_rate) as avg_hr,
                   MAX(heart_rate) as max_hr,
                   MIN(heart_rate) as min_hr,
                   COUNT(*) as record_count
            FROM heart_rate_records
            WHERE profile_id = ? AND recorded_at >= ?
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        if not row or row['avg_hr'] is None:
            return 0.0
        
        avg_hr = row['avg_hr'] or 0
        min_hr = row['min_hr'] or 0
        max_hr = row['max_hr'] or 0
        
        normal_range = (60, 100)
        if normal_range[0] <= avg_hr <= normal_range[1]:
            hr_score = 100
        elif avg_hr < normal_range[0]:
            hr_score = max(0, 100 - (normal_range[0] - avg_hr) * 2)
        else:
            hr_score = max(0, 100 - (avg_hr - normal_range[1]) * 2)
        
        variability_penalty = 0
        if max_hr > 0 and min_hr > 0:
            variability = max_hr - min_hr
            if variability > 50:
                variability_penalty = min(30, (variability - 50) * 0.5)
        
        return max(0, hr_score - variability_penalty)
    
    async def _calculate_bp_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT AVG(systolic) as avg_sys,
                   AVG(diastolic) as avg_dia,
                   COUNT(*) as record_count
            FROM blood_pressure_records
            WHERE profile_id = ? AND recorded_at >= ?
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        if not row or row['avg_sys'] is None:
            return 0.0
        
        avg_sys = row['avg_sys'] or 0
        avg_dia = row['avg_dia'] or 0
        
        if avg_sys < 120 and avg_dia < 80:
            return 100
        elif avg_sys < 130 and avg_dia < 85:
            return 85
        elif avg_sys < 140 and avg_dia < 90:
            return 70
        elif avg_sys < 160 and avg_dia < 100:
            return 50
        else:
            return max(0, 30 - (avg_sys - 160) * 0.3)
    
    async def _calculate_glucose_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT AVG(glucose) as avg_glucose,
                   measure_type,
                   COUNT(*) as record_count
            FROM blood_glucose_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY measure_type
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        rows = cursor.fetchall()
        if not rows:
            return 0.0
        
        scores = []
        for row in rows:
            glucose = row['avg_glucose'] or 0
            measure_type = row['measure_type'] or 'fasting'
            
            if measure_type == 'fasting':
                if glucose < 6.1:
                    score = 100
                elif glucose < 7.0:
                    score = 70
                else:
                    score = max(0, 50 - (glucose - 7.0) * 10)
            else:
                if glucose < 7.8:
                    score = 100
                elif glucose < 11.1:
                    score = 70
                else:
                    score = max(0, 50 - (glucose - 11.1) * 5)
            
            scores.append(score)
        
        return statistics.mean(scores) if scores else 0.0
    
    async def _calculate_weight_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT w.weight, h.height
            FROM weight_records w
            LEFT JOIN health_profiles h ON w.profile_id = h.profile_id
            WHERE w.profile_id = ? AND w.recorded_at >= ?
            ORDER BY w.recorded_at DESC
            LIMIT 1
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        if not row or row['weight'] is None:
            return 0.0
        
        weight = row['weight'] or 0
        height = row['height'] or 0
        
        if height <= 0 or weight <= 0:
            return 0.0
        
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        
        if 18.5 <= bmi < 24:
            return 100
        elif 24 <= bmi < 28:
            return 75
        elif 28 <= bmi < 32:
            return 50
        else:
            return max(0, 30 - abs(bmi - 24) * 2)
    
    async def _calculate_mental_score(self, cursor, profile_id: str, days: int) -> float:
        cursor.execute('''
            SELECT COUNT(*) as meditation_count,
                   SUM(duration_minutes) as total_minutes
            FROM behavior_records
            WHERE profile_id = ? AND behavior_type = 'meditation'
            AND recorded_at >= ?
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        row = cursor.fetchone()
        
        base_score = 70.0
        
        if row and row['meditation_count']:
            meditation_bonus = min(20, row['meditation_count'] * 2)
            base_score += meditation_bonus
        
        return min(100, base_score)
    
    async def _save_health_score(self, profile_id: str, score: HealthScore):
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO health_scores_history
            (profile_id, overall_score, dimensions, level, generated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            profile_id,
            score.overall_score,
            json.dumps(score.dimensions),
            score.level.value,
            score.generated_at
        ))
        
        conn.commit()
    
    async def analyze_spending_insights(self, profile_id: str = None, days: int = 30) -> List[SpendingInsight]:
        conn = self._get_conn()
        c = conn.cursor()
        
        insights = []
        
        c.execute('''
            SELECT category,
                   SUM(amount) as total,
                   AVG(amount) as avg_amount,
                   COUNT(*) as tx_count
            FROM transactions
            WHERE type = 'expense' AND date >= ?
            GROUP BY category
            ORDER BY total DESC
        ''', (datetime.now() - timedelta(days=days),))
        
        category_stats = [dict(row) for row in c.fetchall()]
        
        for stat in category_stats:
            category = stat['category']
            total = stat['total']
            avg = stat['avg_amount']
            
            c.execute('''
                SELECT SUM(amount) as total
                FROM transactions
                WHERE type = 'expense' AND category = ? AND date >= ? AND date < ?
            ''', (category, datetime.now() - timedelta(days=days*2), datetime.now() - timedelta(days=days)))
            
            prev_row = c.fetchone()
            prev_total = prev_row['total'] if prev_row and prev_row['total'] else 0
            
            if prev_total > 0:
                change_percent = (total - prev_total) / prev_total * 100
                if change_percent > 20:
                    trend = "上升明显"
                elif change_percent > 5:
                    trend = "小幅上升"
                elif change_percent < -20:
                    trend = "下降明显"
                elif change_percent < -5:
                    trend = "小幅下降"
                else:
                    trend = "基本持平"
            else:
                trend = "新类别"
            
            anomaly_detected = False
            if avg > 500:
                c.execute('''
                    SELECT amount FROM transactions
                    WHERE type = 'expense' AND category = ? AND date >= ?
                    ORDER BY amount DESC LIMIT 5
                ''', (category, datetime.now() - timedelta(days=days)))
                
                top_amounts = [row['amount'] for row in c.fetchall()]
                if top_amounts:
                    threshold = statistics.mean(top_amounts) * 2
                    if avg > threshold:
                        anomaly_detected = True
            
            savings_potential = 0
            recommendations = []
            
            if category in ['餐饮', '外卖', '零食']:
                savings_potential = total * 0.15
                recommendations.append(f"考虑减少外出就餐次数，每月可节省约{savings_potential:.0f}元")
            elif category in ['购物', '服饰']:
                savings_potential = total * 0.2
                recommendations.append("购买前思考是否真正需要，避免冲动消费")
            elif category in ['娱乐', '游戏']:
                savings_potential = total * 0.25
                recommendations.append("设定娱乐预算上限，寻找免费替代活动")
            elif category in ['交通']:
                savings_potential = total * 0.1
                recommendations.append("考虑公共交通或共享出行方式")
            
            insights.append(SpendingInsight(
                category=category,
                total_amount=round(total, 2),
                average_amount=round(avg, 2),
                trend=trend,
                anomaly_detected=anomaly_detected,
                savings_potential=round(savings_potential, 2),
                recommendations=recommendations
            ))
        
        return insights
    
    async def analyze_behavior_patterns(self, profile_id: str, days: int = 30) -> List[BehaviorPattern]:
        conn = self._get_conn()
        c = conn.cursor()
        
        patterns = []
        
        c.execute('''
            SELECT behavior_type, behavior_name,
                   COUNT(*) as frequency,
                   AVG(duration_minutes) as avg_duration,
                   strftime('%H', start_time) as hour
            FROM behavior_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY behavior_type, behavior_name, hour
            ORDER BY frequency DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        behavior_rows = [dict(row) for row in c.fetchall()]
        
        behavior_groups = defaultdict(list)
        for row in behavior_rows:
            key = (row['behavior_type'], row['behavior_name'])
            behavior_groups[key].append(row)
        
        for (behavior_type, behavior_name), records in behavior_groups.items():
            if not records:
                continue
            
            total_frequency = sum(r['frequency'] for r in records)
            avg_duration = statistics.mean([r['avg_duration'] for r in records if r['avg_duration']])
            
            hour_counts = defaultdict(int)
            for r in records:
                hour_counts[r['hour']] += r['frequency']
            
            typical_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else "12"
            typical_time = f"{typical_hour}:00"
            
            efficiency_score = self._calculate_efficiency_score(behavior_type, avg_duration, total_frequency)
            
            suggestions = self._generate_behavior_suggestions(behavior_type, avg_duration, efficiency_score)
            
            patterns.append(BehaviorPattern(
                pattern_type=behavior_type,
                pattern_name=behavior_name or behavior_type,
                frequency=total_frequency,
                typical_time=typical_time,
                efficiency_score=round(efficiency_score, 1),
                suggestions=suggestions
            ))
        
        commute_patterns = await self._analyze_commute_pattern(c, profile_id, days)
        if commute_patterns:
            patterns.append(commute_patterns)
        
        work_patterns = await self._analyze_work_pattern(c, profile_id, days)
        if work_patterns:
            patterns.append(work_patterns)
        
        return patterns
    
    def _calculate_efficiency_score(self, behavior_type: str, avg_duration: float, frequency: int) -> float:
        base_score = 70.0
        
        if behavior_type in ['work', 'study']:
            if avg_duration and avg_duration > 60:
                base_score += 15
            if frequency and frequency >= 5:
                base_score += 10
        elif behavior_type in ['exercise', 'meditation']:
            if avg_duration and avg_duration >= 30:
                base_score += 15
            if frequency and frequency >= 3:
                base_score += 10
        elif behavior_type in ['entertainment', 'gaming']:
            if avg_duration and avg_duration <= 120:
                base_score += 10
            else:
                base_score -= 10
        
        return min(100, max(0, base_score))
    
    def _generate_behavior_suggestions(self, behavior_type: str, avg_duration: float, efficiency: float) -> List[str]:
        suggestions = []
        
        if efficiency < 60:
            if behavior_type == 'work':
                suggestions.append("尝试番茄工作法提高效率")
                suggestions.append("设置专注时间段，减少干扰")
            elif behavior_type == 'study':
                suggestions.append("考虑使用间隔学习法")
                suggestions.append("定期休息，保持注意力")
            elif behavior_type == 'exercise':
                suggestions.append("设定固定的运动时间表")
                suggestions.append("从简单运动开始，逐步增加强度")
            elif behavior_type == 'entertainment':
                suggestions.append("设定每日娱乐时间上限")
                suggestions.append("选择更有意义的休闲活动")
        elif efficiency >= 80:
            suggestions.append("保持当前的良好习惯")
        
        return suggestions
    
    async def _analyze_commute_pattern(self, cursor, profile_id: str, days: int) -> Optional[BehaviorPattern]:
        cursor.execute('''
            SELECT strftime('%w', recorded_at) as weekday,
                   strftime('%H', recorded_at) as hour,
                   location_name,
                   COUNT(*) as frequency
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            AND (location_type = 'work' OR location_type = 'home')
            GROUP BY weekday, hour, location_type
            ORDER BY frequency DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        rows = cursor.fetchall()
        if not rows:
            return None
        
        commute_times = []
        for row in rows:
            hour = int(row['hour'])
            if 6 <= hour <= 9 or 17 <= hour <= 20:
                commute_times.append(row['hour'])
        
        if not commute_times:
            return None
        
        typical_hour = statistics.mode(commute_times) if commute_times else "8"
        
        return BehaviorPattern(
            pattern_type="commute",
            pattern_name="通勤模式",
            frequency=len(commute_times),
            typical_time=f"{typical_hour}:00",
            efficiency_score=75.0,
            suggestions=["建议提前10-15分钟出发避开高峰", "考虑远程办公或弹性工作时间"]
        )
    
    async def _analyze_work_pattern(self, cursor, profile_id: str, days: int) -> Optional[BehaviorPattern]:
        cursor.execute('''
            SELECT strftime('%H', recorded_at) as hour,
                   COUNT(*) as activity_count
            FROM behavior_records
            WHERE profile_id = ? AND recorded_at >= ?
            AND behavior_type IN ('work', 'meeting', 'study')
            GROUP BY hour
            ORDER BY activity_count DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        rows = cursor.fetchall()
        if not rows:
            return None
        
        productive_hours = [row['hour'] for row in rows[:3]]
        typical_time = f"{productive_hours[0]}:00-{int(productive_hours[0])+2}:00" if productive_hours else "9:00-11:00"
        
        return BehaviorPattern(
            pattern_type="productivity",
            pattern_name="高效时段",
            frequency=len(rows),
            typical_time=typical_time,
            efficiency_score=80.0,
            suggestions=["在高效时段处理重要任务", "避免在高效时段安排会议"]
        )
    
    async def generate_report(self, profile_id: str, report_type: ReportType, 
                             custom_start: datetime = None, custom_end: datetime = None) -> AnalysisReport:
        if report_type == ReportType.DAILY:
            period_days = 1
            period_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = datetime.now()
        elif report_type == ReportType.WEEKLY:
            period_days = 7
            period_start = datetime.now() - timedelta(days=7)
            period_end = datetime.now()
        else:
            period_days = 30
            period_start = datetime.now() - timedelta(days=30)
            period_end = datetime.now()
        
        if custom_start:
            period_start = custom_start
        if custom_end:
            period_end = custom_end
        
        health_score = await self.calculate_health_score(profile_id, period_days)
        spending_insights = await self.analyze_spending_insights(profile_id, period_days)
        behavior_patterns = await self.analyze_behavior_patterns(profile_id, period_days)
        goals_progress = await self._get_goals_progress(profile_id)
        
        personalized_suggestions = await self._generate_personalized_suggestions(
            health_score, spending_insights, behavior_patterns, goals_progress
        )
        
        report = AnalysisReport(
            report_id=self._generate_report_id(),
            report_type=report_type,
            profile_id=profile_id,
            period_start=period_start,
            period_end=period_end,
            health_score=health_score,
            spending_insights=spending_insights,
            behavior_patterns=behavior_patterns,
            goals_progress=goals_progress,
            personalized_suggestions=personalized_suggestions,
            generated_at=datetime.now()
        )
        
        await self._save_report(report)
        
        return report
    
    async def _get_goals_progress(self, profile_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT goal_type, goal_name, target_value, current_value, unit, deadline, status
            FROM user_goals
            WHERE profile_id = ? AND status = 'active'
        ''', (profile_id,))
        
        goals = []
        for row in c.fetchall():
            target = row['target_value'] or 0
            current = row['current_value'] or 0
            progress = (current / target * 100) if target > 0 else 0
            
            goals.append({
                "type": row['goal_type'],
                "name": row['goal_name'],
                "target": target,
                "current": current,
                "unit": row['unit'],
                "progress": round(min(100, progress), 1),
                "deadline": row['deadline'],
                "status": row['status']
            })
        
        return {
            "total_goals": len(goals),
            "completed": len([g for g in goals if g['progress'] >= 100]),
            "in_progress": len([g for g in goals if 0 < g['progress'] < 100]),
            "goals": goals
        }
    
    async def _generate_personalized_suggestions(self, health_score: HealthScore,
                                                  spending_insights: List[SpendingInsight],
                                                  behavior_patterns: List[BehaviorPattern],
                                                  goals_progress: Dict[str, Any]) -> List[str]:
        suggestions = []
        
        if health_score:
            if health_score.overall_score < 60:
                suggestions.append("整体健康状况需要改善，建议进行全面体检")
            elif health_score.overall_score < 75:
                suggestions.append("健康状态良好，但仍有提升空间")
            
            for dim, score in health_score.dimensions.items():
                if score > 0 and score < 60:
                    suggestions.extend(health_score.recommendations[:2])
                    break
        
        high_spending = [s for s in spending_insights if s.total_amount > 1000]
        if high_spending:
            top_category = high_spending[0].category
            suggestions.append(f"建议关注{top_category}支出，考虑优化消费结构")
        
        low_efficiency = [p for p in behavior_patterns if p.efficiency_score < 60]
        if low_efficiency:
            for pattern in low_efficiency[:2]:
                if pattern.suggestions:
                    suggestions.append(pattern.suggestions[0])
        
        if goals_progress.get('in_progress', 0) > 0:
            suggestions.append("继续努力完成设定的目标")
        if goals_progress.get('total_goals', 0) == 0:
            suggestions.append("建议设定一些健康或财务目标，更好地追踪进展")
        
        return suggestions[:5]
    
    async def _save_report(self, report: AnalysisReport):
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO analytics_reports
            (report_id, profile_id, report_type, period_start, period_end,
             health_score, spending_insights, behavior_patterns, goals_progress,
             personalized_suggestions, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.report_id,
            report.profile_id,
            report.report_type.value,
            report.period_start,
            report.period_end,
            json.dumps({
                "overall_score": report.health_score.overall_score if report.health_score else None,
                "level": report.health_score.level.value if report.health_score else None,
                "dimensions": report.health_score.dimensions if report.health_score else None
            }),
            json.dumps([{
                "category": s.category, "total": s.total_amount,
                "trend": s.trend, "anomaly": s.anomaly_detected
            } for s in report.spending_insights]),
            json.dumps([{
                "type": p.pattern_type, "name": p.pattern_name,
                "efficiency": p.efficiency_score
            } for p in report.behavior_patterns]),
            json.dumps(report.goals_progress),
            json.dumps(report.personalized_suggestions),
            report.generated_at
        ))
        
        conn.commit()
        logger.info(f"Report saved: {report.report_id}")
    
    async def set_goal(self, profile_id: str, goal_type: str, goal_name: str,
                      target_value: float, unit: str = None, deadline: str = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO user_goals
            (profile_id, goal_type, goal_name, target_value, unit, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (profile_id, goal_type, goal_name, target_value, unit, deadline))
        
        conn.commit()
        
        return {
            "success": True,
            "goal": {
                "type": goal_type,
                "name": goal_name,
                "target": target_value,
                "unit": unit,
                "deadline": deadline
            }
        }
    
    async def update_goal_progress(self, profile_id: str, goal_name: str, 
                                   current_value: float) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE user_goals
            SET current_value = ?, status = CASE WHEN ? >= target_value THEN 'completed' ELSE status END
            WHERE profile_id = ? AND goal_name = ?
        ''', (current_value, current_value, profile_id, goal_name))
        
        if c.rowcount == 0:
            return {"error": "Goal not found"}
        
        conn.commit()
        
        c.execute('''
            SELECT target_value, status FROM user_goals
            WHERE profile_id = ? AND goal_name = ?
        ''', (profile_id, goal_name))
        
        row = c.fetchone()
        
        return {
            "success": True,
            "goal_name": goal_name,
            "current_value": current_value,
            "target_value": row['target_value'] if row else None,
            "status": row['status'] if row else None
        }
    
    async def record_behavior(self, profile_id: str, behavior_type: str, 
                             behavior_name: str = None, start_time: datetime = None,
                             end_time: datetime = None, duration_minutes: int = None,
                             metadata: Dict = None) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        if not start_time:
            start_time = datetime.now()
        
        c.execute('''
            INSERT INTO behavior_records
            (profile_id, behavior_type, behavior_name, start_time, end_time, 
             duration_minutes, metadata, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_id, behavior_type, behavior_name, start_time, end_time,
            duration_minutes, json.dumps(metadata) if metadata else None, datetime.now()
        ))
        
        conn.commit()
        
        return {
            "success": True,
            "behavior_type": behavior_type,
            "behavior_name": behavior_name,
            "duration_minutes": duration_minutes,
            "recorded_at": datetime.now().isoformat()
        }
    
    async def get_reports(self, profile_id: str, report_type: str = None, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        query = "SELECT * FROM analytics_reports WHERE profile_id = ?"
        params = [profile_id]
        
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        
        query += " ORDER BY generated_at DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        
        reports = []
        for row in c.fetchall():
            report = dict(row)
            for field in ['health_score', 'spending_insights', 'behavior_patterns', 
                         'goals_progress', 'personalized_suggestions']:
                if report.get(field):
                    try:
                        report[field] = json.loads(report[field])
                    except:
                        pass
            reports.append(report)
        
        return reports
    
    async def get_health_score_history(self, profile_id: str, days: int = 90) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT overall_score, dimensions, level, generated_at
            FROM health_scores_history
            WHERE profile_id = ? AND generated_at >= ?
            ORDER BY generated_at DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        history = []
        for row in c.fetchall():
            record = {
                "score": row['overall_score'],
                "level": row['level'],
                "generated_at": row['generated_at']
            }
            if row['dimensions']:
                try:
                    record['dimensions'] = json.loads(row['dimensions'])
                except:
                    pass
            history.append(record)
        
        return history
    
    async def add_insight(self, profile_id: str, insight_type: str, 
                         category: str, title: str, description: str,
                         importance: float = 0.5, action_required: bool = False,
                         valid_days: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        valid_until = datetime.now() + timedelta(days=valid_days)
        
        c.execute('''
            INSERT INTO analysis_insights
            (profile_id, insight_type, insight_category, title, description,
             importance, action_required, valid_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (profile_id, insight_type, category, title, description,
              importance, 1 if action_required else 0, valid_until))
        
        conn.commit()
        
        return {
            "success": True,
            "insight": {
                "type": insight_type,
                "category": category,
                "title": title,
                "importance": importance,
                "valid_until": valid_until.isoformat()
            }
        }
    
    async def get_active_insights(self, profile_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM analysis_insights
            WHERE profile_id = ? AND is_dismissed = 0 AND valid_until >= ?
            ORDER BY importance DESC, created_at DESC
        ''', (profile_id, datetime.now()))
        
        return [dict(row) for row in c.fetchall()]
    
    async def dismiss_insight(self, insight_id: int) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('UPDATE analysis_insights SET is_dismissed = 1 WHERE id = ?', (insight_id,))
        
        if c.rowcount == 0:
            return {"error": "Insight not found"}
        
        conn.commit()
        
        return {"success": True, "insight_id": insight_id}
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[AdvancedAnalyticsService] = None


def get_service() -> AdvancedAnalyticsService:
    global _service_instance
    if _service_instance is None:
        _service_instance = AdvancedAnalyticsService()
    return _service_instance


async def get_health_score(profile_id: str, days: int = 30) -> Dict[str, Any]:
    service = get_service()
    score = await service.calculate_health_score(profile_id, days)
    return {
        "overall_score": score.overall_score,
        "level": score.level.value,
        "dimensions": score.dimensions,
        "recommendations": score.recommendations,
        "generated_at": score.generated_at.isoformat()
    }


async def get_spending_insights(profile_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
    service = get_service()
    insights = await service.analyze_spending_insights(profile_id, days)
    return [{
        "category": i.category,
        "total_amount": i.total_amount,
        "average_amount": i.average_amount,
        "trend": i.trend,
        "anomaly_detected": i.anomaly_detected,
        "savings_potential": i.savings_potential,
        "recommendations": i.recommendations
    } for i in insights]


async def get_behavior_patterns(profile_id: str, days: int = 30) -> List[Dict[str, Any]]:
    service = get_service()
    patterns = await service.analyze_behavior_patterns(profile_id, days)
    return [{
        "pattern_type": p.pattern_type,
        "pattern_name": p.pattern_name,
        "frequency": p.frequency,
        "typical_time": p.typical_time,
        "efficiency_score": p.efficiency_score,
        "suggestions": p.suggestions
    } for p in patterns]


async def generate_report(profile_id: str, report_type: str = "weekly") -> Dict[str, Any]:
    service = get_service()
    rt = ReportType(report_type) if report_type in [r.value for r in ReportType] else ReportType.WEEKLY
    report = await service.generate_report(profile_id, rt)
    
    return {
        "report_id": report.report_id,
        "report_type": report.report_type.value,
        "period": {
            "start": report.period_start.isoformat(),
            "end": report.period_end.isoformat()
        },
        "health_score": {
            "overall_score": report.health_score.overall_score if report.health_score else None,
            "level": report.health_score.level.value if report.health_score else None,
            "dimensions": report.health_score.dimensions if report.health_score else None
        } if report.health_score else None,
        "spending_insights": [{
            "category": s.category, "total_amount": s.total_amount,
            "trend": s.trend, "savings_potential": s.savings_potential
        } for s in report.spending_insights],
        "behavior_patterns": [{
            "type": p.pattern_type, "name": p.pattern_name,
            "efficiency_score": p.efficiency_score
        } for p in report.behavior_patterns],
        "goals_progress": report.goals_progress,
        "personalized_suggestions": report.personalized_suggestions,
        "generated_at": report.generated_at.isoformat()
    }


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = AdvancedAnalyticsService(':memory:')
        
        print("=== 高级分析报告服务测试 ===\n")
        
        profile_id = "test_profile_001"
        
        print("1. 计算健康评分...")
        score = await service.calculate_health_score(profile_id, 30)
        print(f"   综合评分: {score.overall_score}")
        print(f"   评级: {score.level.value}")
        print(f"   各维度: {score.dimensions}")
        
        print("\n2. 分析消费洞察...")
        insights = await service.analyze_spending_insights(profile_id, 30)
        print(f"   消费类别数: {len(insights)}")
        for i in insights[:3]:
            print(f"   - {i.category}: {i.total_amount}元 ({i.trend})")
        
        print("\n3. 分析行为模式...")
        patterns = await service.analyze_behavior_patterns(profile_id, 30)
        print(f"   行为模式数: {len(patterns)}")
        for p in patterns:
            print(f"   - {p.pattern_name}: 效率{p.efficiency_score}分")
        
        print("\n4. 设置目标...")
        goal = await service.set_goal(profile_id, "health", "每日步数", 10000, "步")
        print(f"   目标设置: {goal}")
        
        print("\n5. 生成周报...")
        report = await service.generate_report(profile_id, ReportType.WEEKLY)
        print(f"   报告ID: {report.report_id}")
        print(f"   健康评分: {report.health_score.overall_score if report.health_score else 'N/A'}")
        print(f"   个性化建议: {len(report.personalized_suggestions)}条")
        
        print("\n6. 记录行为...")
        behavior = await service.record_behavior(
            profile_id, "exercise", "跑步", 
            duration_minutes=30,
            metadata={"calories": 300}
        )
        print(f"   行为记录: {behavior}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())