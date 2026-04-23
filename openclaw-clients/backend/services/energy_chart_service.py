import logging
logger = logging.getLogger(__name__)
"""
能源图表生成服务
功能：
- 用电趋势图数据（日/周/月）
- 设备占比饼图数据
- 电费对比柱状图数据
- 节能进度环形图数据
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import math


class EnergyChartService:
    def __init__(self, db_path: str = "family_assistant.db"):
        self.db_path = db_path
        self.electricity_rate = 0.4887  # 电价
    
    def get_daily_trend_data(self, date: str = None) -> Dict:
        """
        获取每日用电趋势数据（按小时）
        返回适合折线图的数据
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 按小时统计用电量
        cursor.execute('''
            SELECT 
                strftime('%H', recorded_at) as hour,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost,
                COUNT(*) as record_count
            FROM energy_records
            WHERE DATE(recorded_at) = ?
            GROUP BY hour
            ORDER BY hour
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 填充 24 小时数据
        hour_data = {str(i).zfill(2): {'kwh': 0, 'cost': 0, 'count': 0} for i in range(24)}
        
        for row in rows:
            hour = row[0]
            hour_data[hour] = {
                'kwh': round(row[1] or 0, 2),
                'cost': round((row[1] or 0) * self.electricity_rate, 2),
                'count': row[2] or 0
            }
        
        # 转换为图表格式
        labels = [f"{h}:00" for h in range(24)]
        kwh_values = [hour_data[str(h).zfill(2)]['kwh'] for h in range(24)]
        cost_values = [hour_data[str(h).zfill(2)]['cost'] for h in range(24)]
        
        return {
            'success': True,
            'date': date,
            'labels': labels,
            'datasets': [
                {
                    'label': '用电量 (度)',
                    'data': kwh_values,
                    'borderColor': '#4CAF50',
                    'backgroundColor': 'rgba(76, 175, 80, 0.1)',
                    'tension': 0.4
                },
                {
                    'label': '电费 (元)',
                    'data': cost_values,
                    'borderColor': '#2196F3',
                    'backgroundColor': 'rgba(33, 150, 243, 0.1)',
                    'tension': 0.4,
                    'yAxisID': 'y1'
                }
            ],
            'peak_hour': max(range(24), key=lambda h: kwh_values[h]),
            'total_kwh': sum(kwh_values),
            'total_cost': sum(cost_values)
        }
    
    def get_weekly_trend_data(self, end_date: str = None) -> Dict:
        """
        获取每周用电趋势数据（按天）
        """
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        start_date = end_date - timedelta(days=6)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 按天统计
        cursor.execute('''
            SELECT 
                DATE(recorded_at) as date,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost
            FROM energy_records
            WHERE DATE(recorded_at) >= ? AND DATE(recorded_at) <= ?
            GROUP BY DATE(recorded_at)
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 填充 7 天数据
        date_data = {}
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            date_data[date_str] = {'kwh': 0, 'cost': 0}
            current += timedelta(days=1)
        
        for row in rows:
            date_str = row[0]
            if date_str in date_data:
                date_data[date_str] = {
                    'kwh': round(row[1] or 0, 2),
                    'cost': round(row[2] or 0, 2)
                }
        
        # 转换为图表格式
        labels = []
        kwh_values = []
        cost_values = []
        
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%m/%d'))
            kwh_values.append(date_data[date_str]['kwh'])
            cost_values.append(date_data[date_str]['cost'])
            current += timedelta(days=1)
        
        return {
            'success': True,
            'period': f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}",
            'labels': labels,
            'datasets': [
                {
                    'label': '用电量 (度)',
                    'data': kwh_values,
                    'backgroundColor': '#4CAF50',
                    'borderColor': '#388E3C',
                    'borderWidth': 1
                },
                {
                    'label': '电费 (元)',
                    'data': cost_values,
                    'backgroundColor': '#2196F3',
                    'borderColor': '#1976D2',
                    'borderWidth': 1
                }
            ],
            'total_kwh': sum(kwh_values),
            'total_cost': sum(cost_values),
            'avg_daily_kwh': round(sum(kwh_values) / 7, 2)
        }
    
    def get_monthly_trend_data(self, year: int = None, month: int = None) -> Dict:
        """
        获取月度用电趋势数据（按天）
        """
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        # 获取当月天数
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        start_date = datetime(year, month, 1)
        end_date = next_month - timedelta(days=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                DATE(recorded_at) as date,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost
            FROM energy_records
            WHERE DATE(recorded_at) >= ? AND DATE(recorded_at) <= ?
            GROUP BY DATE(recorded_at)
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 填充整月数据
        days_in_month = (next_month - start_date).days
        date_data = {}
        current = start_date
        while current < next_month:
            date_str = current.strftime('%Y-%m-%d')
            date_data[date_str] = {'kwh': 0, 'cost': 0}
            current += timedelta(days=1)
        
        for row in rows:
            date_str = row[0]
            if date_str in date_data:
                date_data[date_str] = {
                    'kwh': round(row[1] or 0, 2),
                    'cost': round(row[2] or 0, 2)
                }
        
        # 转换为图表格式（每 5 天一个标签，避免太密集）
        labels = []
        kwh_values = []
        cost_values = []
        
        current = start_date
        i = 0
        while current < next_month:
            date_str = current.strftime('%Y-%m-%d')
            if i % 5 == 0:
                labels.append(current.strftime('%m/%d'))
            else:
                labels.append('')
            kwh_values.append(date_data[date_str]['kwh'])
            cost_values.append(date_data[date_str]['cost'])
            current += timedelta(days=1)
            i += 1
        
        return {
            'success': True,
            'period': f"{year}年{month}月",
            'labels': labels,
            'datasets': [
                {
                    'label': '用电量 (度)',
                    'data': kwh_values,
                    'backgroundColor': '#4CAF50',
                    'borderColor': '#388E3C',
                    'borderWidth': 1,
                    'fill': True
                }
            ],
            'total_kwh': sum(kwh_values),
            'total_cost': sum(cost_values),
            'avg_daily_kwh': round(sum(kwh_values) / days_in_month, 2)
        }
    
    def get_device_distribution_data(self, date: str = None) -> Dict:
        """
        获取设备用电占比数据（饼图）
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 按设备统计
        cursor.execute('''
            SELECT 
                device_name,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost,
                COUNT(*) as usage_count
            FROM energy_records
            WHERE DATE(recorded_at) = ?
            GROUP BY device_id
            ORDER BY total_kwh DESC
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为饼图数据
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4CAF50', '#2196F3'
        ]
        
        labels = []
        data = []
        background_colors = []
        
        total_kwh = 0
        for i, row in enumerate(rows):
            device_name = row[0]
            kwh = row[1] or 0
            total_kwh += kwh
            
            labels.append(device_name)
            data.append(round(kwh, 2))
            background_colors.append(colors[i % len(colors)])
        
        # 计算百分比
        percentages = []
        for kwh in data:
            if total_kwh > 0:
                percentages.append(round(kwh / total_kwh * 100, 1))
            else:
                percentages.append(0)
        
        return {
            'success': True,
            'date': date,
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': background_colors,
                'borderColor': '#FFFFFF',
                'borderWidth': 2
            }],
            'percentages': percentages,
            'total_kwh': round(total_kwh, 2)
        }
    
    def get_cost_comparison_data(self, months: int = 6) -> Dict:
        """
        获取电费对比数据（柱状图）
        比较最近 N 个月的电费
        """
        now = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        labels = []
        data = []
        
        for i in range(months - 1, -1, -1):
            target_date = now - timedelta(days=i * 30)
            year = target_date.year
            month = target_date.month
            
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            
            start_date = datetime(year, month, 1)
            
            cursor.execute('''
                SELECT SUM(cost) FROM energy_records
                WHERE recorded_at >= ? AND recorded_at < ?
            ''', (start_date.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d')))
            
            result = cursor.fetchone()
            cost = result[0] or 0
            
            labels.append(f"{month}月")
            data.append(round(cost, 2))
        
        conn.close()
        
        # 计算平均值
        avg_cost = sum(data) / len(data) if data else 0
        
        return {
            'success': True,
            'period': f'最近{months}个月',
            'labels': labels,
            'datasets': [{
                'label': '电费 (元)',
                'data': data,
                'backgroundColor': [
                    '#FF6384' if cost > avg_cost * 1.2 else
                    '#4CAF50' if cost < avg_cost * 0.8 else
                    '#2196F3'
                    for cost in data
                ],
                'borderColor': '#FFFFFF',
                'borderWidth': 2
            }],
            'average': round(avg_cost, 2),
            'max': max(data) if data else 0,
            'min': min(data) if data else 0
        }
    
    def get_saving_goal_progress_data(self, goal_id: int = None) -> Dict:
        """
        获取节能目标进度数据（环形图）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if goal_id:
            cursor.execute('''
                SELECT goal_name, target_kwh, current_kwh, target_cost, current_cost
                FROM energy_saving_goals
                WHERE id = ? AND is_active = 1
            ''', (goal_id,))
        else:
            cursor.execute('''
                SELECT goal_name, target_kwh, current_kwh, target_cost, current_cost
                FROM energy_saving_goals
                WHERE is_active = 1
                ORDER BY id DESC LIMIT 1
            ''')
        
        goal = cursor.fetchone()
        conn.close()
        
        if not goal:
            return {'success': False, 'message': '无活跃节能目标'}
        
        goal_name, target_kwh, current_kwh, target_cost, current_cost = goal
        
        # 计算进度
        progress = (current_kwh / target_kwh * 100) if target_kwh > 0 else 0
        remaining = target_kwh - current_kwh
        
        # 环形图数据
        if progress <= 100:
            colors = ['#4CAF50', '#E0E0E0']  # 绿色 + 灰色
            data = [current_kwh, max(0, remaining)]
        else:
            colors = ['#F44336', '#E0E0E0']  # 红色 + 灰色
            data = [target_kwh, current_kwh - target_kwh]
        
        return {
            'success': True,
            'goal_name': goal_name,
            'target_kwh': round(target_kwh, 2),
            'target_cost': round(target_cost, 2),
            'current_kwh': round(current_kwh, 2),
            'current_cost': round(current_cost, 2),
            'progress': round(progress, 1),
            'remaining_kwh': round(max(0, remaining), 2),
            'on_track': progress <= 100,
            'chart': {
                'labels': ['已完成', '剩余'] if progress <= 100 else ['目标', '超出'],
                'datasets': [{
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': '#FFFFFF',
                    'borderWidth': 2
                }]
            }
        }
    
    def get_energy_report_chart_data(self, period: str = 'daily', **kwargs) -> Dict:
        """
        获取综合图表数据
        period: 'daily' | 'weekly' | 'monthly'
        """
        if period == 'daily':
            date = kwargs.get('date')
            trend = self.get_daily_trend_data(date)
            distribution = self.get_device_distribution_data(date)
            
            return {
                'success': True,
                'period': 'daily',
                'trend': trend,
                'distribution': distribution
            }
        
        elif period == 'weekly':
            end_date = kwargs.get('end_date')
            trend = self.get_weekly_trend_data(end_date)
            
            return {
                'success': True,
                'period': 'weekly',
                'trend': trend
            }
        
        elif period == 'monthly':
            year = kwargs.get('year')
            month = kwargs.get('month')
            trend = self.get_monthly_trend_data(year, month)
            cost_comparison = self.get_cost_comparison_data(6)
            
            return {
                'success': True,
                'period': 'monthly',
                'trend': trend,
                'cost_comparison': cost_comparison
            }
        
        else:
            return {'success': False, 'message': '不支持的周期类型'}


# 快捷函数
def quick_chart_data(chart_type: str, **kwargs):
    """快速获取图表数据"""
    service = EnergyChartService()
    
    if chart_type == 'daily_trend':
        return service.get_daily_trend_data(kwargs.get('date'))
    elif chart_type == 'weekly_trend':
        return service.get_weekly_trend_data(kwargs.get('end_date'))
    elif chart_type == 'monthly_trend':
        return service.get_monthly_trend_data(kwargs.get('year'), kwargs.get('month'))
    elif chart_type == 'device_distribution':
        return service.get_device_distribution_data(kwargs.get('date'))
    elif chart_type == 'cost_comparison':
        return service.get_cost_comparison_data(kwargs.get('months', 6))
    elif chart_type == 'goal_progress':
        return service.get_saving_goal_progress_data(kwargs.get('goal_id'))
    else:
        return {'success': False, 'message': '未知的图表类型'}


if __name__ == "__main__":
    # 测试
    service = EnergyChartService()
    
    logger.info("=== 每日趋势 ===")
    trend = service.get_daily_trend_data()
    logger.info(f"峰值时段：{trend['peak_hour']}:00")
    logger.info(f"总用电：{trend['total_kwh']:.2f}度")
    
    logger.info("\n=== 设备分布 ===")
    dist = service.get_device_distribution_data()
    for i, label in enumerate(dist['labels']):
        logger.info(f"{label}: {dist['data'][i]}度 ({dist['percentages'][i]}%)")
    
    logger.info("\n=== 电费对比 ===")
    comparison = service.get_cost_comparison_data(6)
    logger.info(f"平均电费：{comparison['average']}元/月")
    logger.info(f"最高：{comparison['max']}元，最低：{comparison['min']}元")
