#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势预测服务
健康趋势、消费趋势、位置模式预测
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class PredictionType(Enum):
    HEALTH_STEPS = "health_steps"
    HEALTH_SLEEP = "health_sleep"
    HEALTH_HEART_RATE = "health_heart_rate"
    HEALTH_WEIGHT = "health_weight"
    HEALTH_BLOOD_PRESSURE = "health_blood_pressure"
    HEALTH_BLOOD_GLUCOSE = "health_blood_glucose"
    
    EXPENSE_MONTHLY = "expense_monthly"
    EXPENSE_CATEGORY = "expense_category"
    EXPENSE_BUDGET = "expense_budget"
    
    LOCATION_COMMUTE = "location_commute"
    LOCATION_PATTERN = "location_pattern"
    LOCATION_FREQUENCY = "location_frequency"


@dataclass
class Prediction:
    prediction_type: PredictionType
    direction: TrendDirection
    confidence: float
    current_value: Any
    predicted_value: Any
    change_percent: float
    period_days: int
    trend_data: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    predicted_at: datetime


class TrendPredictionService:
    """趋势预测服务"""
    
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
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT UNIQUE,
                profile_id TEXT,
                prediction_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL,
                current_value TEXT,
                predicted_value TEXT,
                change_percent REAL,
                period_days INTEGER,
                trend_data TEXT,
                insights TEXT,
                recommendations TEXT,
                valid_until TIMESTAMP,
                predicted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS prediction_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                prediction_type TEXT NOT NULL,
                model_params TEXT,
                accuracy_score REAL,
                last_trained TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(profile_id, prediction_type)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS commute_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT,
                day_of_week INTEGER,
                hour INTEGER,
                location_name TEXT,
                location_type TEXT,
                frequency INTEGER,
                avg_duration_minutes INTEGER,
                last_occurred TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_predictions_profile ON predictions(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_commute_profile ON commute_patterns(profile_id)')
        self._conn.commit()
        logger.info("Trend prediction service database initialized")
    
    def _generate_prediction_id(self) -> str:
        import uuid
        return f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _calculate_trend(self, values: List[float]) -> Tuple[TrendDirection, float]:
        """计算趋势方向和置信度"""
        if len(values) < 2:
            return TrendDirection.STABLE, 0.0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return TrendDirection.STABLE, 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        y_pred = [slope * xi + (sum_y - slope * sum_x) / n for xi in x]
        ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = max(0, min(1, r_squared))
        
        if abs(slope) < 0.01 * abs(y_mean) if y_mean != 0 else True:
            return TrendDirection.STABLE, confidence
        elif slope > 0:
            return TrendDirection.UP, confidence
        else:
            return TrendDirection.DOWN, confidence
    
    def _predict_next_values(self, values: List[float], periods: int = 7) -> List[float]:
        """预测未来值（简单线性外推）"""
        if len(values) < 2:
            return values * periods
        
        n = len(values)
        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return [values[-1]] * periods
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        predictions = []
        for i in range(periods):
            pred = slope * (n + i) + intercept
            predictions.append(max(0, pred))
        
        return predictions
    
    async def predict_health_trends(self, profile_id: str, days: int = 30) -> Dict[str, Prediction]:
        """预测健康趋势"""
        predictions = {}
        
        predictions['steps'] = await self._predict_steps(profile_id, days)
        predictions['sleep'] = await self._predict_sleep(profile_id, days)
        predictions['heart_rate'] = await self._predict_heart_rate(profile_id, days)
        predictions['weight'] = await self._predict_weight(profile_id, days)
        predictions['blood_pressure'] = await self._predict_blood_pressure(profile_id, days)
        predictions['blood_glucose'] = await self._predict_blood_glucose(profile_id, days)
        
        for pred in predictions.values():
            if pred:
                await self._save_prediction(profile_id, pred)
        
        return predictions
    
    async def _predict_steps(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测步数趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, SUM(steps) as total_steps
            FROM exercise_records
            WHERE profile_id = ? AND steps IS NOT NULL AND recorded_at >= ?
            GROUP BY date(recorded_at)
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 7:
            return None
        
        values = [r['total_steps'] for r in reversed(records[-30:])]
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_avg = statistics.mean(predicted)
        
        current_avg = statistics.mean(values[-7:])
        change_percent = (predicted_avg - current_avg) / current_avg * 100 if current_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        if direction == TrendDirection.DOWN:
            insights.append("近期步数呈下降趋势")
            if predicted_avg < 5000:
                recommendations.append("建议每天增加步行活动，目标8000-10000步")
            else:
                recommendations.append("保持当前运动量，注意循序渐进")
        elif direction == TrendDirection.UP:
            insights.append("近期步数呈上升趋势，运动量增加")
            recommendations.append("继续保持良好的运动习惯")
        else:
            insights.append("步数保持稳定")
            if current_avg < 5000:
                recommendations.append("建议适当增加日常步行量")
        
        trend_data = [{"date": records[-30+i]['day'] if i < len(records) else None,
                       "value": v} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_STEPS,
            direction=direction,
            confidence=confidence,
            current_value=round(current_avg),
            predicted_value=round(predicted_avg),
            change_percent=round(change_percent, 1),
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_sleep(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测睡眠趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, 
                   AVG(duration_minutes) as avg_duration,
                   AVG(sleep_quality) as avg_quality
            FROM sleep_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY date(recorded_at)
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 7:
            return None
        
        values = [r['avg_duration'] for r in reversed(records[-30:])]
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_avg = statistics.mean(predicted)
        
        current_avg = statistics.mean(values[-7:])
        change_percent = (predicted_avg - current_avg) / current_avg * 100 if current_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        optimal_sleep = 480
        
        if predicted_avg < optimal_sleep * 0.8:
            insights.append(f"预测睡眠时长不足，预计平均 {predicted_avg/60:.1f} 小时")
            recommendations.append("建议调整作息，保证7-8小时睡眠")
            recommendations.append("睡前避免使用电子设备")
        elif predicted_avg > optimal_sleep * 1.2:
            insights.append(f"预测睡眠时间过长，可能影响精力")
            recommendations.append("建议保持规律的作息时间")
        else:
            insights.append("睡眠时长在正常范围内")
            recommendations.append("继续保持良好的睡眠习惯")
        
        if direction == TrendDirection.DOWN:
            insights.append("睡眠时间呈下降趋势，需注意")
        
        trend_data = [{"date": records[-30+i]['day'] if i < len(records) else None,
                       "value": round(v, 0)} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_SLEEP,
            direction=direction,
            confidence=confidence,
            current_value=round(current_avg),
            predicted_value=round(predicted_avg),
            change_percent=round(change_percent, 1),
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_heart_rate(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测心率趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, AVG(heart_rate) as avg_hr
            FROM heart_rate_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY date(recorded_at)
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        values = [r['avg_hr'] for r in reversed(records[-30:])]
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_avg = statistics.mean(predicted)
        
        current_avg = statistics.mean(values[-7:])
        change_percent = (predicted_avg - current_avg) / current_avg * 100 if current_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        normal_min, normal_max = 60, 100
        
        if predicted_avg < normal_min:
            insights.append(f"预测心率偏低: {predicted_avg:.0f} bpm")
            recommendations.append("建议咨询医生，排除病理性原因")
        elif predicted_avg > normal_max:
            insights.append(f"预测心率偏高: {predicted_avg:.0f} bpm")
            recommendations.append("建议减少咖啡因摄入，增加有氧运动")
        else:
            insights.append("心率预测值在正常范围内")
        
        if direction == TrendDirection.UP and change_percent > 10:
            insights.append("心率呈明显上升趋势")
            recommendations.append("建议关注是否有压力或焦虑")
        
        trend_data = [{"date": records[-30+i]['day'] if i < len(records) else None,
                       "value": round(v, 0)} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_HEART_RATE,
            direction=direction,
            confidence=confidence,
            current_value=round(current_avg),
            predicted_value=round(predicted_avg),
            change_percent=round(change_percent, 1),
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_weight(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测体重趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, weight
            FROM weight_records
            WHERE profile_id = ? AND recorded_at >= ?
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*3)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        daily_weights = {}
        for r in records:
            day = r['day']
            if day not in daily_weights:
                daily_weights[day] = []
            daily_weights[day].append(r['weight'])
        
        daily_avg = {day: statistics.mean(weights) for day, weights in daily_weights.items()}
        sorted_days = sorted(daily_avg.keys())
        values = [daily_avg[day] for day in sorted_days[-30:]]
        
        if len(values) < 5:
            return None
        
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_avg = statistics.mean(predicted)
        
        current_avg = statistics.mean(values[-7:])
        change_percent = (predicted_avg - current_avg) / current_avg * 100 if current_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        if abs(change_percent) > 5:
            if direction == TrendDirection.UP:
                insights.append(f"预测体重将增加，预计变化 {change_percent:.1f}%")
                recommendations.append("建议控制饮食，增加运动量")
            else:
                insights.append(f"预测体重将下降，预计变化 {abs(change_percent):.1f}%")
                if change_percent < -10:
                    recommendations.append("体重下降较快，建议确认是否在健康范围内")
        else:
            insights.append("体重预测保持稳定")
        
        trend_data = [{"date": sorted_days[-30+i] if i < len(sorted_days) else None,
                       "value": round(v, 1)} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_WEIGHT,
            direction=direction,
            confidence=confidence,
            current_value=round(current_avg, 1),
            predicted_value=round(predicted_avg, 1),
            change_percent=round(change_percent, 1),
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_blood_pressure(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测血压趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, 
                   AVG(systolic) as avg_systolic,
                   AVG(diastolic) as avg_diastolic
            FROM blood_pressure_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY date(recorded_at)
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        systolic_values = [r['avg_systolic'] for r in reversed(records[-30:])]
        diastolic_values = [r['avg_diastolic'] for r in reversed(records[-30:])]
        
        sys_direction, sys_confidence = self._calculate_trend(systolic_values)
        dia_direction, dia_confidence = self._calculate_trend(diastolic_values)
        
        predicted_sys = self._predict_next_values(systolic_values[-7:], 7)
        predicted_dia = self._predict_next_values(diastolic_values[-7:], 7)
        
        current_sys = statistics.mean(systolic_values[-7:])
        current_dia = statistics.mean(diastolic_values[-7:])
        predicted_sys_avg = statistics.mean(predicted_sys)
        predicted_dia_avg = statistics.mean(predicted_dia)
        
        insights = []
        recommendations = []
        
        if predicted_sys_avg >= 140 or predicted_dia_avg >= 90:
            insights.append(f"预测血压偏高: {predicted_sys_avg:.0f}/{predicted_dia_avg:.0f} mmHg")
            recommendations.append("建议减少盐分摄入，控制体重")
            recommendations.append("定期监测血压，必要时就医")
        elif predicted_sys_avg < 90 or predicted_dia_avg < 60:
            insights.append(f"预测血压偏低: {predicted_sys_avg:.0f}/{predicted_dia_avg:.0f} mmHg")
            recommendations.append("注意营养均衡，避免突然起身")
        else:
            insights.append("血压预测值在正常范围内")
        
        confidence = (sys_confidence + dia_confidence) / 2
        
        trend_data = [{"date": records[-30+i]['day'] if i < len(records) else None,
                       "systolic": round(s, 0), "diastolic": round(d, 0)} 
                      for i, (s, d) in enumerate(zip(systolic_values, diastolic_values))]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_BLOOD_PRESSURE,
            direction=sys_direction,
            confidence=confidence,
            current_value=f"{current_sys:.0f}/{current_dia:.0f}",
            predicted_value=f"{predicted_sys_avg:.0f}/{predicted_dia_avg:.0f}",
            change_percent=0,
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_blood_glucose(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测血糖趋势"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT date(recorded_at) as day, 
                   AVG(glucose) as avg_glucose,
                   measure_type
            FROM blood_glucose_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY date(recorded_at), measure_type
            ORDER BY day DESC
        ''', (profile_id, datetime.now() - timedelta(days=days*2)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        fasting_records = [r for r in records if r['measure_type'] == 'fasting']
        
        if not fasting_records:
            fasting_records = records
        
        values = [r['avg_glucose'] for r in reversed(fasting_records[-30:])]
        
        if len(values) < 3:
            return None
        
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_avg = statistics.mean(predicted)
        
        current_avg = statistics.mean(values[-7:])
        change_percent = (predicted_avg - current_avg) / current_avg * 100 if current_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        if predicted_avg >= 7.0:
            insights.append(f"预测空腹血糖偏高: {predicted_avg:.1f} mmol/L")
            recommendations.append("建议控制碳水化合物摄入")
            recommendations.append("增加运动量，定期复查")
        elif predicted_avg >= 6.1:
            insights.append(f"预测空腹血糖在临界范围: {predicted_avg:.1f} mmol/L")
            recommendations.append("注意饮食控制，预防糖尿病")
        else:
            insights.append("血糖预测值在正常范围内")
        
        if direction == TrendDirection.UP:
            insights.append("血糖呈上升趋势，需关注")
        
        trend_data = [{"date": fasting_records[-30+i]['day'] if i < len(fasting_records) else None,
                       "value": round(v, 1)} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.HEALTH_BLOOD_GLUCOSE,
            direction=direction,
            confidence=confidence,
            current_value=round(current_avg, 1),
            predicted_value=round(predicted_avg, 1),
            change_percent=round(change_percent, 1),
            period_days=7,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def predict_expense_trends(self, profile_id: str = None, days: int = 30) -> Dict[str, Prediction]:
        """预测消费趋势"""
        predictions = {}
        
        predictions['monthly'] = await self._predict_monthly_expense(profile_id, days)
        predictions['category'] = await self._predict_category_expense(profile_id, days)
        predictions['budget'] = await self._predict_budget_status(profile_id)
        
        for pred in predictions.values():
            if pred:
                await self._save_prediction(profile_id, pred)
        
        return predictions
    
    async def _predict_monthly_expense(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测月度消费"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT strftime('%Y-%m-%d', date) as day, 
                   SUM(amount) as total
            FROM transactions
            WHERE type = 'expense' AND date >= ?
            GROUP BY strftime('%Y-%m-%d', date)
            ORDER BY day DESC
        ''', (datetime.now() - timedelta(days=days*2),))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 7:
            return None
        
        values = [r['total'] for r in reversed(records[-30:])]
        direction, confidence = self._calculate_trend(values)
        
        predicted = self._predict_next_values(values[-7:], 7)
        predicted_total = sum(predicted)
        predicted_daily_avg = statistics.mean(predicted)
        
        current_total = sum(values[-7:])
        current_daily_avg = statistics.mean(values[-7:])
        
        days_remaining = 30 - datetime.now().day
        month_predicted = current_total + predicted_daily_avg * days_remaining
        
        change_percent = (predicted_daily_avg - current_daily_avg) / current_daily_avg * 100 if current_daily_avg > 0 else 0
        
        insights = []
        recommendations = []
        
        if direction == TrendDirection.UP:
            insights.append(f"消费呈上升趋势，日均增加 {abs(change_percent):.1f}%")
            if change_percent > 20:
                recommendations.append("建议审视最近的大额支出")
        elif direction == TrendDirection.DOWN:
            insights.append(f"消费呈下降趋势，日均减少 {abs(change_percent):.1f}%")
        else:
            insights.append("消费保持稳定")
        
        insights.append(f"预计本月总支出约 {month_predicted:.0f}元")
        
        trend_data = [{"date": records[-30+i]['day'] if i < len(records) else None,
                       "value": round(v, 0)} for i, v in enumerate(values)]
        
        return Prediction(
            prediction_type=PredictionType.EXPENSE_MONTHLY,
            direction=direction,
            confidence=confidence,
            current_value=round(current_total),
            predicted_value=round(month_predicted),
            change_percent=round(change_percent, 1),
            period_days=30,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_category_expense(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测分类消费"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type = 'expense' AND date >= ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT 5
        ''', (datetime.now() - timedelta(days=days),))
        
        records = [dict(row) for row in c.fetchall()]
        
        if not records:
            return None
        
        top_category = records[0]
        category_name = top_category['category']
        category_total = top_category['total']
        
        c.execute('''
            SELECT strftime('%Y-%m-%d', date) as day, SUM(amount) as total
            FROM transactions
            WHERE type = 'expense' AND category = ? AND date >= ?
            GROUP BY strftime('%Y-%m-%d', date)
            ORDER BY day DESC
        ''', (category_name, datetime.now() - timedelta(days=days*2)))
        
        daily_records = [dict(row) for row in c.fetchall()]
        
        insights = [f"最高消费类别: {category_name}，累计 {category_total:.0f}元"]
        recommendations = []
        
        if len(daily_records) >= 7:
            values = [r['total'] for r in reversed(daily_records[-14:])]
            direction, confidence = self._calculate_trend(values)
            
            if direction == TrendDirection.UP:
                insights.append(f"{category_name}消费呈上升趋势")
                recommendations.append(f"建议关注{category_name}支出是否合理")
        else:
            direction = TrendDirection.STABLE
            confidence = 0
        
        trend_data = [{"category": r['category'], "value": round(r['total'], 0)} for r in records]
        
        return Prediction(
            prediction_type=PredictionType.EXPENSE_CATEGORY,
            direction=direction,
            confidence=confidence,
            current_value=category_total,
            predicted_value=category_total,
            change_percent=0,
            period_days=days,
            trend_data=trend_data,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_budget_status(self, profile_id: str) -> Optional[Prediction]:
        """预测预算状态"""
        conn = self._get_conn()
        c = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
        
        c.execute('''
            SELECT category, amount as budget
            FROM budgets
            WHERE month = ?
        ''', (current_month,))
        
        budgets = [dict(row) for row in c.fetchall()]
        
        if not budgets:
            return None
        
        c.execute('''
            SELECT category, SUM(amount) as spent
            FROM transactions
            WHERE type = 'expense' AND date LIKE ?
            GROUP BY category
        ''', (f"{current_month}%",))
        
        spent = {row['category']: row['spent'] for row in c.fetchall()}
        
        days_passed = datetime.now().day
        days_in_month = 30
        days_remaining = days_in_month - days_passed
        
        insights = []
        recommendations = []
        budget_status = []
        
        for budget in budgets:
            category = budget['category']
            budget_amount = budget['budget']
            spent_amount = spent.get(category, 0)
            remaining = budget_amount - spent_amount
            usage_percent = spent_amount / budget_amount * 100 if budget_amount > 0 else 0
            
            daily_budget = remaining / days_remaining if days_remaining > 0 else 0
            
            budget_status.append({
                "category": category,
                "budget": budget_amount,
                "spent": spent_amount,
                "remaining": remaining,
                "usage_percent": round(usage_percent, 1),
                "daily_budget": round(daily_budget, 0)
            })
            
            if usage_percent > 100:
                insights.append(f"{category}已超预算 {usage_percent-100:.1f}%")
            elif usage_percent > 80:
                insights.append(f"{category}已用预算 {usage_percent:.1f}%")
                recommendations.append(f"建议控制{category}支出，剩余日均可用 {daily_budget:.0f}元")
        
        direction = TrendDirection.STABLE
        confidence = 0.8
        
        return Prediction(
            prediction_type=PredictionType.EXPENSE_BUDGET,
            direction=direction,
            confidence=confidence,
            current_value=budget_status,
            predicted_value=None,
            change_percent=0,
            period_days=days_remaining,
            trend_data=budget_status,
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def predict_location_patterns(self, profile_id: str, days: int = 30) -> Dict[str, Prediction]:
        """预测位置模式"""
        predictions = {}
        
        predictions['commute'] = await self._predict_commute_time(profile_id, days)
        predictions['pattern'] = await self._predict_location_pattern(profile_id, days)
        predictions['frequency'] = await self._predict_location_frequency(profile_id, days)
        
        for pred in predictions.values():
            if pred:
                await self._save_prediction(profile_id, pred)
        
        return predictions
    
    async def _predict_commute_time(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测通勤时间"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT strftime('%w', recorded_at) as weekday,
                   strftime('%H:%M', recorded_at) as time,
                   location_name,
                   location_type,
                   COUNT(*) as frequency
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY weekday, time, location_name
            HAVING frequency >= 2
            ORDER BY frequency DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        commute_patterns = {}
        for r in records:
            weekday = int(r['weekday'])
            hour = int(r['time'].split(':')[0])
            location_type = r['location_type'] or 'other'
            
            if location_type in ['work', 'office', 'company', 'school', 'home']:
                key = (weekday, hour)
                if key not in commute_patterns:
                    commute_patterns[key] = {'count': 0, 'locations': []}
                commute_patterns[key]['count'] += r['frequency']
                commute_patterns[key]['locations'].append(r['location_name'])
        
        insights = []
        recommendations = []
        
        morning_commute = sorted([k for k in commute_patterns.keys() 
                                  if 6 <= k[1] <= 9 and k[0] not in [0, 6]], 
                                 key=lambda x: commute_patterns[x]['count'], reverse=True)
        evening_commute = sorted([k for k in commute_patterns.keys() 
                                  if 17 <= k[1] <= 21 and k[0] not in [0, 6]], 
                                 key=lambda x: commute_patterns[x]['count'], reverse=True)
        
        if morning_commute:
            pattern = morning_commute[0]
            weekday_names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
            insights.append(f"早高峰通勤时间: {weekday_names[pattern[0]]} {pattern[1]}:00 左右")
            recommendations.append("建议提前10-15分钟出发，避开高峰")
        
        if evening_commute:
            pattern = evening_commute[0]
            weekday_names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
            insights.append(f"晚高峰通勤时间: {weekday_names[pattern[0]]} {pattern[1]}:00 左右")
        
        c.execute('''
            INSERT OR REPLACE INTO commute_patterns
            (profile_id, day_of_week, hour, location_name, location_type, frequency)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (profile_id, morning_commute[0][0] if morning_commute else 0,
              morning_commute[0][1] if morning_commute else 8,
              commute_patterns[morning_commute[0]]['locations'][0] if morning_commute else '',
              'commute', commute_patterns[morning_commute[0]]['count'] if morning_commute else 0))
        conn.commit()
        
        trend_data = [{"weekday": k[0], "hour": k[1], "count": v['count'],
                       "locations": v['locations'][:3]} for k, v in commute_patterns.items()]
        
        return Prediction(
            prediction_type=PredictionType.LOCATION_COMMUTE,
            direction=TrendDirection.STABLE,
            confidence=0.7,
            current_value=morning_commute[0][1] if morning_commute else 8,
            predicted_value=morning_commute[0][1] if morning_commute else 8,
            change_percent=0,
            period_days=days,
            trend_data=trend_data[:10],
            insights=insights,
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_location_pattern(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测位置模式"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT strftime('%w', recorded_at) as weekday,
                   strftime('%H', recorded_at) as hour,
                   location_name,
                   COUNT(*) as frequency
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY weekday, hour, location_name
            HAVING frequency >= 3
            ORDER BY frequency DESC
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 5:
            return None
        
        weekday_names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
        
        patterns = {}
        for r in records:
            weekday = int(r['weekday'])
            hour = int(r['hour'])
            location = r['location_name']
            key = (weekday, hour)
            
            if key not in patterns:
                patterns[key] = {}
            if location not in patterns[key]:
                patterns[key][location] = 0
            patterns[key][location] += r['frequency']
        
        insights = []
        recommendations = []
        
        top_patterns = sorted(patterns.items(), key=lambda x: sum(x[1].values()), reverse=True)[:5]
        
        for (weekday, hour), locations in top_patterns:
            top_location = max(locations.items(), key=lambda x: x[1])
            insights.append(f"{weekday_names[weekday]} {hour}:00 通常在 {top_location[0]}")
        
        if len(insights) == 0:
            return None
        
        trend_data = [{"weekday": k[0], "hour": k[1], 
                       "locations": [{"name": loc, "count": cnt} for loc, cnt in v.items()]}
                      for k, v in patterns.items()]
        
        return Prediction(
            prediction_type=PredictionType.LOCATION_PATTERN,
            direction=TrendDirection.STABLE,
            confidence=0.75,
            current_value=top_patterns[0][1] if top_patterns else {},
            predicted_value=top_patterns[0][1] if top_patterns else {},
            change_percent=0,
            period_days=days,
            trend_data=trend_data[:10],
            insights=insights[:5],
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _predict_location_frequency(self, profile_id: str, days: int) -> Optional[Prediction]:
        """预测位置频率"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT location_name,
                   COUNT(*) as visit_count
            FROM location_records
            WHERE profile_id = ? AND recorded_at >= ?
            GROUP BY location_name
            ORDER BY visit_count DESC
            LIMIT 10
        ''', (profile_id, datetime.now() - timedelta(days=days)))
        
        records = [dict(row) for row in c.fetchall()]
        
        if len(records) < 3:
            return None
        
        total_visits = sum(r['visit_count'] for r in records)
        
        insights = [f"过去{days}天内最常去的地点:"]
        recommendations = []
        
        top_locations = records[:5]
        for i, loc in enumerate(top_locations, 1):
            percent = loc['visit_count'] / total_visits * 100
            insights.append(f"{i}. {loc['location_name']} ({loc['visit_count']}次, {percent:.1f}%)")
        
        trend_data = [{"location": r['location_name'], "count": r['visit_count'],
                       "percent": round(r['visit_count'] / total_visits * 100, 1)} 
                      for r in records]
        
        return Prediction(
            prediction_type=PredictionType.LOCATION_FREQUENCY,
            direction=TrendDirection.STABLE,
            confidence=0.8,
            current_value=top_locations[0]['location_name'] if top_locations else None,
            predicted_value=top_locations[0]['location_name'] if top_locations else None,
            change_percent=0,
            period_days=days,
            trend_data=trend_data,
            insights=insights[:6],
            recommendations=recommendations,
            predicted_at=datetime.now()
        )
    
    async def _save_prediction(self, profile_id: str, prediction: Prediction):
        """保存预测结果"""
        import json
        conn = self._get_conn()
        c = conn.cursor()
        
        prediction_id = self._generate_prediction_id()
        
        c.execute('''
            INSERT INTO predictions
            (prediction_id, profile_id, prediction_type, direction, confidence,
             current_value, predicted_value, change_percent, period_days,
             trend_data, insights, recommendations, predicted_at, valid_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id,
            profile_id,
            prediction.prediction_type.value,
            prediction.direction.value,
            prediction.confidence,
            str(prediction.current_value) if prediction.current_value else None,
            str(prediction.predicted_value) if prediction.predicted_value else None,
            prediction.change_percent,
            prediction.period_days,
            json.dumps(prediction.trend_data),
            json.dumps(prediction.insights),
            json.dumps(prediction.recommendations),
            prediction.predicted_at,
            prediction.predicted_at + timedelta(days=1)
        ))
        
        conn.commit()
        logger.info(f"Prediction saved: {prediction.prediction_type.value}")
    
    async def get_predictions(self, profile_id: str = None, prediction_type: str = None,
                              days: int = 7) -> List[Dict[str, Any]]:
        """获取预测结果"""
        import json
        conn = self._get_conn()
        c = conn.cursor()
        
        query = "SELECT * FROM predictions WHERE valid_until >= ?"
        params = [datetime.now()]
        
        if profile_id:
            query += " AND profile_id = ?"
            params.append(profile_id)
        if prediction_type:
            query += " AND prediction_type = ?"
            params.append(prediction_type)
        
        query += " ORDER BY predicted_at DESC"
        
        c.execute(query, params)
        
        predictions = []
        for row in c.fetchall():
            pred = dict(row)
            for field in ['trend_data', 'insights', 'recommendations']:
                if pred.get(field):
                    try:
                        pred[field] = json.loads(pred[field])
                    except:
                        pass
            predictions.append(pred)
        
        return predictions
    
    async def run_all_predictions(self, profile_id: str, days: int = 30) -> Dict[str, Any]:
        """运行所有预测"""
        health_predictions = await self.predict_health_trends(profile_id, days)
        expense_predictions = await self.predict_expense_trends(profile_id, days)
        location_predictions = await self.predict_location_patterns(profile_id, days)
        
        def serialize_predictions(preds: Dict[str, Prediction]) -> List[Dict]:
            result = []
            for key, pred in preds.items():
                if pred:
                    result.append({
                        "type": key,
                        "prediction_type": pred.prediction_type.value,
                        "direction": pred.direction.value,
                        "confidence": pred.confidence,
                        "current_value": pred.current_value,
                        "predicted_value": pred.predicted_value,
                        "change_percent": pred.change_percent,
                        "insights": pred.insights,
                        "recommendations": pred.recommendations
                    })
            return result
        
        summary = {
            "profile_id": profile_id,
            "generated_at": datetime.now().isoformat(),
            "health": serialize_predictions(health_predictions),
            "expense": serialize_predictions(expense_predictions),
            "location": serialize_predictions(location_predictions),
            "total_predictions": len(health_predictions) + len(expense_predictions) + len(location_predictions)
        }
        
        return summary
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[TrendPredictionService] = None


def get_service() -> TrendPredictionService:
    global _service_instance
    if _service_instance is None:
        _service_instance = TrendPredictionService()
    return _service_instance


async def predict_health_trends(profile_id: str, days: int = 30) -> Dict[str, Any]:
    service = get_service()
    predictions = await service.predict_health_trends(profile_id, days)
    return {k: {"type": v.prediction_type.value, "direction": v.direction.value,
                "confidence": v.confidence, "predicted_value": v.predicted_value,
                "insights": v.insights} for k, v in predictions.items() if v}


async def predict_expense_trends(profile_id: str = None, days: int = 30) -> Dict[str, Any]:
    service = get_service()
    predictions = await service.predict_expense_trends(profile_id, days)
    return {k: {"type": v.prediction_type.value, "direction": v.direction.value,
                "confidence": v.confidence, "predicted_value": v.predicted_value,
                "insights": v.insights} for k, v in predictions.items() if v}


async def predict_location_patterns(profile_id: str, days: int = 30) -> Dict[str, Any]:
    service = get_service()
    predictions = await service.predict_location_patterns(profile_id, days)
    return {k: {"type": v.prediction_type.value, "direction": v.direction.value,
                "confidence": v.confidence, "predicted_value": v.predicted_value,
                "insights": v.insights} for k, v in predictions.items() if v}


async def get_predictions(**kwargs) -> List[Dict[str, Any]]:
    return await get_service().get_predictions(**kwargs)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = TrendPredictionService(':memory:')
        
        print("=== 趋势预测服务测试 ===\n")
        
        print("1. 预测健康趋势...")
        health = await service.predict_health_trends("test_profile")
        print(f"   预测类型: {list(health.keys())}")
        
        print("\n2. 预测消费趋势...")
        expense = await service.predict_expense_trends("test_profile")
        print(f"   预测类型: {list(expense.keys())}")
        
        print("\n3. 预测位置模式...")
        location = await service.predict_location_patterns("test_profile")
        print(f"   预测类型: {list(location.keys())}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())