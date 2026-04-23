import logging
logger = logging.getLogger(__name__)
"""
AI 用电预测服务
功能：
- 基于历史数据预测未来用电
- 月度电费预测
- 异常用电检测
- 智能节能建议
- 用电模式分析
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math
from collections import defaultdict


class AIEnergyPredictor:
    def __init__(self, db_path: str = "family_assistant.db"):
        self.db_path = db_path
        self.electricity_rate = 0.4887  # 电价
        
        # 预测模型参数
        self.model_params = {
            'weekday_factor': {},  # 星期系数
            'hour_factor': {},     # 小时系数
            'trend_slope': 0,      # 长期趋势
            'baseline': 0          # 基础用电量
        }
    
    def _load_historical_data(self, days: int = 30) -> List[Dict]:
        """加载历史用电数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                device_name,
                power_watts,
                usage_hours,
                energy_kwh,
                cost,
                recorded_at,
                room
            FROM energy_records
            WHERE recorded_at >= ?
            ORDER BY recorded_at
        ''', (start_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'device_name': row[0],
                'power_watts': row[1],
                'usage_hours': row[2],
                'energy_kwh': row[3],
                'cost': row[4],
                'recorded_at': row[5],
                'room': row[6]
            })
        
        return data
    
    def _aggregate_daily_data(self, historical_data: List[Dict]) -> Dict[str, float]:
        """按天聚合用电数据"""
        daily_data = defaultdict(float)
        
        for record in historical_data:
            date = record['recorded_at'][:10]  # YYYY-MM-DD
            daily_data[date] += record['energy_kwh']
        
        return dict(daily_data)
    
    def _calculate_time_factors(self, historical_data: List[Dict]):
        """计算时间系数（星期、小时）"""
        # 星期系数
        weekday_totals = defaultdict(float)
        weekday_counts = defaultdict(int)
        
        # 小时系数
        hour_totals = defaultdict(float)
        hour_counts = defaultdict(int)
        
        for record in historical_data:
            timestamp = datetime.fromisoformat(record['recorded_at'].replace('Z', '+00:00'))
            weekday = timestamp.weekday()
            hour = timestamp.hour
            
            weekday_totals[weekday] += record['energy_kwh']
            weekday_counts[weekday] += 1
            
            hour_totals[hour] += record['energy_kwh']
            hour_counts[hour] += 1
        
        # 计算平均
        overall_avg = sum(weekday_totals.values()) / max(1, sum(weekday_counts.values()))
        
        self.model_params['weekday_factor'] = {
            wd: (weekday_totals[wd] / max(1, weekday_counts[wd])) / max(0.1, overall_avg)
            for wd in range(7)
        }
        
        self.model_params['hour_factor'] = {
            h: (hour_totals[h] / max(1, hour_counts[h])) / max(0.1, overall_avg)
            for h in range(24)
        }
    
    def _calculate_trend(self, daily_data: Dict[str, float]) -> float:
        """计算长期趋势斜率"""
        if len(daily_data) < 7:
            return 0
        
        # 简单线性回归
        dates = sorted(daily_data.keys())
        values = [daily_data[d] for d in dates]
        
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def train_model(self, days: int = 30):
        """训练预测模型"""
        historical_data = self._load_historical_data(days)
        
        if len(historical_data) < 10:
            return {'success': False, 'message': '历史数据不足，需要至少 10 条记录'}
        
        # 计算时间系数
        self._calculate_time_factors(historical_data)
        
        # 聚合日数据
        daily_data = self._aggregate_daily_data(historical_data)
        
        # 计算趋势
        self.model_params['trend_slope'] = self._calculate_trend(daily_data)
        
        # 计算基线
        self.model_params['baseline'] = sum(daily_data.values()) / max(1, len(daily_data))
        
        return {
            'success': True,
            'message': '模型训练完成',
            'training_days': len(daily_data),
            'baseline_kwh': round(self.model_params['baseline'], 2),
            'trend': round(self.model_params['trend_slope'], 4)
        }
    
    def predict_daily_usage(self, days_ahead: int = 7) -> Dict:
        """
        预测未来 N 天的每日用电量
        """
        if self.model_params['baseline'] == 0:
            self.train_model()
        
        predictions = []
        today = datetime.now()
        
        for i in range(days_ahead):
            future_date = today + timedelta(days=i)
            weekday = future_date.weekday()
            
            # 基础预测
            predicted_kwh = self.model_params['baseline']
            
            # 应用星期系数
            weekday_factor = self.model_params['weekday_factor'].get(weekday, 1.0)
            predicted_kwh *= weekday_factor
            
            # 应用趋势
            predicted_kwh += self.model_params['trend_slope'] * i
            
            # 确保非负
            predicted_kwh = max(0, predicted_kwh)
            
            predictions.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'weekday': future_date.strftime('%A'),
                'predicted_kwh': round(predicted_kwh, 2),
                'predicted_cost': round(predicted_kwh * self.electricity_rate, 2),
                'confidence': min(0.95, 0.7 + 0.05 * (days_ahead - i))  # 越近越准确
            })
        
        total_kwh = sum(p['predicted_kwh'] for p in predictions)
        total_cost = sum(p['predicted_cost'] for p in predictions)
        
        return {
            'success': True,
            'predictions': predictions,
            'total_kwh': round(total_kwh, 2),
            'total_cost': round(total_cost, 2),
            'avg_daily_kwh': round(total_kwh / days_ahead, 2)
        }
    
    def predict_monthly_bill(self, month: int = None, year: int = None) -> Dict:
        """
        预测月度电费
        """
        now = datetime.now()
        if month is None:
            month = now.month
        if year is None:
            year = now.year
        
        # 获取当月天数
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        days_in_month = (next_month - datetime(year, month, 1)).days
        
        # 获取当月已过天数
        passed_days = (now - datetime(year, month, 1)).days if year == now.year and month == now.month else 0
        
        # 预测未来用电
        daily_prediction = self.predict_daily_usage(days_in_month)
        
        # 如果当月已过部分天数，调整预测
        if passed_days > 0:
            historical_data = self._load_historical_data(passed_days)
            daily_data = self._aggregate_daily_data(historical_data)
            
            actual_kwh = sum(v for k, v in daily_data.items() if k.startswith(f'{year}-{month:02d}'))
            
            # 结合实际情况调整
            remaining_days = days_in_month - passed_days
            predicted_remaining = sum(
                p['predicted_kwh'] for p in daily_prediction['predictions'][:remaining_days]
            )
            
            total_kwh = actual_kwh + predicted_remaining
        else:
            total_kwh = daily_prediction['total_kwh']
        
        total_cost = total_kwh * self.electricity_rate
        
        # 与上月对比
        last_month = month - 1 if month > 1 else 12
        last_month_year = year if month > 1 else year - 1
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if last_month == 12:
            start_date = f'{last_month_year}-12-01'
            end_date = f'{last_month_year + 1}-01-01'
        else:
            start_date = f'{last_month_year}-{last_month:02d}-01'
            end_date = f'{last_month_year}-{last_month + 1:02d}-01'
        
        cursor.execute('''
            SELECT SUM(energy_kwh), SUM(cost) FROM energy_records
            WHERE recorded_at >= ? AND recorded_at < ?
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        last_month_kwh = result[0] or 0
        last_month_cost = result[1] or 0
        
        conn.close()
        
        month_over_month_change = ((total_kwh - last_month_kwh) / max(0.1, last_month_kwh)) * 100 if last_month_kwh > 0 else 0
        
        return {
            'success': True,
            'period': f'{year}年{month}月',
            'predicted_kwh': round(total_kwh, 2),
            'predicted_cost': round(total_cost, 2),
            'last_month_kwh': round(last_month_kwh, 2),
            'last_month_cost': round(last_month_cost, 2),
            'month_over_month_change': round(month_over_month_change, 1),
            'trend': 'up' if month_over_month_change > 5 else 'down' if month_over_month_change < -5 else 'stable',
            'days_in_month': days_in_month,
            'passed_days': passed_days
        }
    
    def detect_anomalies(self, days: int = 7) -> Dict:
        """
        检测异常用电模式
        """
        historical_data = self._load_historical_data(days)
        daily_data = self._aggregate_daily_data(historical_data)
        
        if len(daily_data) < 3:
            return {'success': False, 'message': '数据不足'}
        
        values = list(daily_data.values())
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        
        anomalies = []
        
        for date, kwh in daily_data.items():
            # Z-score 检测
            z_score = (kwh - mean) / max(0.1, std)
            
            if abs(z_score) > 2:  # 超过 2 个标准差
                anomalies.append({
                    'date': date,
                    'kwh': round(kwh, 2),
                    'z_score': round(z_score, 2),
                    'type': 'high' if z_score > 0 else 'low',
                    'deviation': round((kwh - mean) / max(0.1, mean) * 100, 1),
                    'severity': 'warning' if abs(z_score) < 3 else 'critical'
                })
        
        # 按严重程度排序
        anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)
        
        return {
            'success': True,
            'analysis_period': f'{days}天',
            'mean_daily_kwh': round(mean, 2),
            'std_kwh': round(std, 2),
            'anomalies_count': len(anomalies),
            'anomalies': anomalies,
            'recommendations': self._generate_anomaly_recommendations(anomalies)
        }
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict]) -> List[str]:
        """生成异常用电建议"""
        recommendations = []
        
        high_anomalies = [a for a in anomalies if a['type'] == 'high']
        
        if len(high_anomalies) > 0:
            recommendations.append(f"检测到{len(high_anomalies)}天用电异常偏高，建议检查是否有电器未关闭")
        
        if any(a['severity'] == 'critical' for a in anomalies):
            recommendations.append("⚠️ 发现严重异常用电，可能存在电器故障或漏电风险")
        
        if len(anomalies) == 0:
            recommendations.append("✅ 用电模式正常，继续保持良好习惯")
        
        return recommendations
    
    def get_smart_suggestions(self) -> Dict:
        """
        基于预测和模式分析生成智能节能建议
        """
        # 获取预测
        prediction = self.predict_daily_usage(7)
        
        # 获取异常检测
        anomalies = self.detect_anomalies(7)
        
        # 获取历史数据
        historical_data = self._load_historical_data(30)
        
        # 分析设备使用模式
        device_usage = defaultdict(lambda: {'kwh': 0, 'hours': 0, 'count': 0})
        for record in historical_data:
            device = record['device_name']
            device_usage[device]['kwh'] += record['energy_kwh']
            device_usage[device]['hours'] += record['usage_hours']
            device_usage[device]['count'] += 1
        
        suggestions = []
        
        # 高耗电设备建议
        for device, usage in sorted(device_usage.items(), key=lambda x: x[1]['kwh'], reverse=True)[:3]:
            avg_daily = usage['kwh'] / max(1, usage['count'])
            if avg_daily > 5:  # 日均超过 5 度
                suggestions.append({
                    'type': 'high_consumption',
                    'priority': 'high',
                    'device': device,
                    'message': f"{device}日均用电{avg_daily:.1f}度，考虑优化使用习惯",
                    'potential_saving': round(avg_daily * 0.2 * self.electricity_rate, 2),
                    'tips': self._get_device_tips(device)
                })
        
        # 预测建议
        if prediction['total_kwh'] > self.model_params['baseline'] * 7 * 1.2:
            suggestions.append({
                'type': 'prediction_warning',
                'priority': 'medium',
                'message': f"预计未来 7 天用电{prediction['total_kwh']:.1f}度，可能超出正常水平",
                'potential_saving': round((prediction['total_kwh'] - self.model_params['baseline'] * 7) * 0.1 * self.electricity_rate, 2)
            })
        
        # 异常建议
        if anomalies.get('anomalies_count', 0) > 0:
            suggestions.extend([{
                'type': 'anomaly_alert',
                'priority': 'high',
                'message': rec
            } for rec in anomalies.get('recommendations', [])])
        
        return {
            'success': True,
            'suggestions': suggestions,
            'total_potential_saving': round(sum(s.get('potential_saving', 0) for s in suggestions), 2)
        }
    
    def _get_device_tips(self, device: str) -> List[str]:
        """获取设备节能技巧"""
        tips_map = {
            '空调': [
                '设定温度不低于 26°C',
                '定期清洗滤网',
                '配合风扇使用可提高制冷效率',
                '外出前提前关闭'
            ],
            '热水器': [
                '不用时关闭电源',
                '设定温度 50-60°C 即可',
                '定期除垢提高加热效率'
            ],
            '冰箱': [
                '不要频繁开关门',
                '食物不要塞太满',
                '定期除霜',
                '远离热源'
            ],
            '电视': [
                '调低屏幕亮度',
                '启用节能模式',
                '不看时彻底断电'
            ],
            '洗衣机': [
                '集中洗涤，满载运行',
                '选择合适水位',
                '尽量使用冷水洗涤'
            ]
        }
        
        for key, tips in tips_map.items():
            if key in device:
                return tips
        
        return ['合理安排使用时间', '不用时彻底断电', '定期维护保养']


# 快捷函数
def quick_predict(predict_type: str, **kwargs):
    """快速获取预测结果"""
    predictor = AIEnergyPredictor()
    
    if predict_type == 'train':
        return predictor.train_model(kwargs.get('days', 30))
    elif predict_type == 'daily':
        return predictor.predict_daily_usage(kwargs.get('days', 7))
    elif predict_type == 'monthly':
        return predictor.predict_monthly_bill(kwargs.get('month'), kwargs.get('year'))
    elif predict_type == 'anomalies':
        return predictor.detect_anomalies(kwargs.get('days', 7))
    elif predict_type == 'suggestions':
        return predictor.get_smart_suggestions()
    else:
        return {'success': False, 'message': '未知的预测类型'}


if __name__ == "__main__":
    # 测试
    predictor = AIEnergyPredictor()
    
    logger.info("=== 训练模型 ===")
    result = predictor.train_model(30)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    logger.info("\n=== 未来 7 天预测 ===")
    prediction = predictor.predict_daily_usage(7)
    for p in prediction['predictions']:
        logger.info(f"{p['date']} ({p['weekday']}): {p['predicted_kwh']}度 ¥{p['predicted_cost']}")
    
    logger.info("\n=== 月度电费预测 ===")
    bill = predictor.predict_monthly_bill()
    logger.info(f"预测电费：¥{bill['predicted_cost']} (上月：¥{bill['last_month_cost']}, 变化：{bill['month_over_month_change']}%)")
    
    logger.info("\n=== 异常检测 ===")
    anomalies = predictor.detect_anomalies(7)
    logger.info(f"发现{anomalies.get('anomalies_count', 0)}个异常")
    
    logger.info("\n=== 智能建议 ===")
    suggestions = predictor.get_smart_suggestions()
    for s in suggestions['suggestions']:
        logger.info(f"- {s['message']}")
