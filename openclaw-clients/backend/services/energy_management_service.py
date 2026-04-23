import logging
logger = logging.getLogger(__name__)
"""
家庭能源管理服务
功能：
- 设备用电监控
- 电费统计与分析
- 节能建议生成
- 用电报告（日报/周报/月报）
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class EnergyManagementService:
    def __init__(self, db_path: str = "family_assistant.db"):
        self.db_path = db_path
        self.init_database()
        
        # 设备功率参考值（瓦特）
        self.device_power_reference = {
            'light': 10,  # LED 灯
            'air_conditioner': 1500,  # 空调
            'tv': 150,  # 电视
            'refrigerator': 200,  # 冰箱
            'washing_machine': 500,  # 洗衣机
            'microwave': 1000,  # 微波炉
            'electric_kettle': 1800,  # 电水壶
            'computer': 300,  # 电脑
            'router': 10,  # 路由器
            'heater': 2000,  # 电暖器
            'fan': 50,  # 风扇
            'water_heater': 3000,  # 热水器
        }
        
        # 电价（元/度）- 可根据地区调整
        self.electricity_rate = 0.4887  # 北京居民电价
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用电记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energy_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                device_name TEXT,
                power_watts REAL,
                usage_hours REAL,
                energy_kwh REAL,
                cost REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                room TEXT,
                notes TEXT
            )
        ''')
        
        # 每日用电统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_energy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_kwh REAL,
                total_cost REAL,
                peak_hour INTEGER,
                peak_kwh REAL,
                device_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 节能目标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energy_saving_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT,
                target_kwh REAL,
                target_cost REAL,
                period TEXT,
                start_date TEXT,
                end_date TEXT,
                current_kwh REAL DEFAULT 0,
                current_cost REAL DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_energy_usage(self, device_id: str, device_name: str, 
                           power_watts: float, usage_hours: float,
                           room: str = None, notes: str = None) -> Dict:
        """
        记录设备用电
        
        Args:
            device_id: 设备 ID
            device_name: 设备名称
            power_watts: 功率（瓦特）
            usage_hours: 使用时长（小时）
            room: 房间
            notes: 备注
        
        Returns:
            记录结果
        """
        # 计算用电量和费用
        energy_kwh = (power_watts * usage_hours) / 1000  # 度
        cost = energy_kwh * self.electricity_rate
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO energy_records 
            (device_id, device_name, power_watts, usage_hours, energy_kwh, cost, room, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (device_id, device_name, power_watts, usage_hours, energy_kwh, cost, room, notes))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 更新每日统计
        self._update_daily_stats()
        
        return {
            'success': True,
            'record_id': record_id,
            'energy_kwh': round(energy_kwh, 3),
            'cost': round(cost, 2)
        }
    
    def _update_daily_stats(self, date: str = None):
        """更新每日用电统计"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算当日统计
        cursor.execute('''
            SELECT 
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost,
                COUNT(DISTINCT device_id) as device_count
            FROM energy_records
            WHERE DATE(recorded_at) = ?
        ''', (date,))
        
        result = cursor.fetchone()
        total_kwh = result[0] or 0
        total_cost = result[0] or 0
        device_count = result[2] or 0
        
        # 计算用电高峰时段
        cursor.execute('''
            SELECT 
                strftime('%H', recorded_at) as hour,
                SUM(energy_kwh) as kwh
            FROM energy_records
            WHERE DATE(recorded_at) = ?
            GROUP BY hour
            ORDER BY kwh DESC
            LIMIT 1
        ''', (date,))
        
        peak_result = cursor.fetchone()
        peak_hour = int(peak_result[0]) if peak_result else 0
        peak_kwh = peak_result[1] if peak_result else 0
        
        # 保存或更新统计
        cursor.execute('''
            INSERT OR REPLACE INTO daily_energy_stats 
            (date, total_kwh, total_cost, peak_hour, peak_kwh, device_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, total_kwh, total_cost, peak_hour, peak_kwh, device_count))
        
        conn.commit()
        conn.close()
    
    def get_daily_report(self, date: str = None) -> Dict:
        """获取每日用电报告"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当日统计
        cursor.execute('''
            SELECT * FROM daily_energy_stats WHERE date = ?
        ''', (date,))
        
        stats = cursor.fetchone()
        
        # 获取设备用电明细
        cursor.execute('''
            SELECT 
                device_name,
                room,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost,
                COUNT(*) as usage_count
            FROM energy_records
            WHERE DATE(recorded_at) = ?
            GROUP BY device_id
            ORDER BY total_kwh DESC
        ''', (date,))
        
        devices = cursor.fetchall()
        
        conn.close()
        
        if not stats:
            return {'success': False, 'message': '当日无用电记录'}
        
        return {
            'success': True,
            'date': date,
            'total_kwh': round(stats[2], 2),
            'total_cost': round(stats[3], 2),
            'peak_hour': stats[4],
            'peak_kwh': round(stats[5], 2),
            'device_count': stats[6],
            'devices': [
                {
                    'name': d[0],
                    'room': d[1],
                    'kwh': round(d[2], 2),
                    'cost': round(d[3], 2),
                    'count': d[4]
                }
                for d in devices
            ]
        }
    
    def get_monthly_report(self, year: int = None, month: int = None) -> Dict:
        """获取月度用电报告"""
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 月度统计
        cursor.execute('''
            SELECT 
                SUM(total_kwh) as total_kwh,
                SUM(total_cost) as total_cost,
                AVG(total_kwh) as avg_daily_kwh,
                AVG(total_cost) as avg_daily_cost
            FROM daily_energy_stats
            WHERE date >= ? AND date < ?
        ''', (start_date, end_date))
        
        stats = cursor.fetchone()
        
        # 每日趋势
        cursor.execute('''
            SELECT date, total_kwh, total_cost
            FROM daily_energy_stats
            WHERE date >= ? AND date < ?
            ORDER BY date
        ''', (start_date, end_date))
        
        daily_trend = cursor.fetchall()
        
        # 设备排名
        cursor.execute('''
            SELECT 
                device_name,
                SUM(energy_kwh) as total_kwh,
                SUM(cost) as total_cost
            FROM energy_records
            WHERE recorded_at >= ? AND recorded_at < ?
            GROUP BY device_id
            ORDER BY total_kwh DESC
            LIMIT 10
        ''', (start_date, end_date))
        
        top_devices = cursor.fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'period': f"{year}年{month}月",
            'total_kwh': round(stats[0] or 0, 2),
            'total_cost': round(stats[1] or 0, 2),
            'avg_daily_kwh': round(stats[2] or 0, 2),
            'avg_daily_cost': round(stats[3] or 0, 2),
            'daily_trend': [
                {'date': d[0], 'kwh': round(d[1], 2), 'cost': round(d[2], 2)}
                for d in daily_trend
            ],
            'top_devices': [
                {'name': d[0], 'kwh': round(d[1], 2), 'cost': round(d[2], 2)}
                for d in top_devices
            ]
        }
    
    def get_energy_saving_suggestions(self) -> List[Dict]:
        """生成节能建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        suggestions = []
        
        # 分析高耗电设备
        cursor.execute('''
            SELECT 
                device_name,
                SUM(energy_kwh) as total_kwh,
                SUM(usage_hours) as total_hours,
                AVG(power_watts) as avg_power
            FROM energy_records
            WHERE recorded_at >= datetime('now', '-7 days')
            GROUP BY device_id
            ORDER BY total_kwh DESC
            LIMIT 5
        ''')
        
        high_power_devices = cursor.fetchall()
        
        for device in high_power_devices:
            name, kwh, hours, power = device
            
            if power > 1500:  # 大功率设备
                suggestions.append({
                    'type': 'high_power',
                    'device': name,
                    'suggestion': f"{name}是大功率设备（{power:.0f}W），建议合理使用，避免长时间开启",
                    'potential_saving': round(kwh * 0.1 * self.electricity_rate, 2)
                })
            
            if hours > 8:  # 长时间使用
                suggestions.append({
                    'type': 'long_usage',
                    'device': name,
                    'suggestion': f"{name}本周使用{hours:.1f}小时，考虑是否需要这么久",
                    'potential_saving': round(kwh * 0.15 * self.electricity_rate, 2)
                })
        
        # 分析用电高峰
        cursor.execute('''
            SELECT 
                strftime('%H', recorded_at) as hour,
                SUM(energy_kwh) as kwh
            FROM energy_records
            WHERE recorded_at >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY kwh DESC
            LIMIT 3
        ''')
        
        peak_hours = cursor.fetchall()
        
        if peak_hours:
            peak_hour_list = [int(h[0]) for h in peak_hours]
            suggestions.append({
                'type': 'peak_hours',
                'hours': peak_hour_list,
                'suggestion': f"用电高峰时段：{', '.join([f'{h}:00' for h in peak_hour_list])}，可考虑错峰用电",
                'potential_saving': 0
            })
        
        # 待机能耗提醒
        suggestions.append({
            'type': 'standby',
            'suggestion': "不用的电器建议拔掉插头，待机能耗约占家庭用电的 5-10%",
            'potential_saving': 5.0
        })
        
        conn.close()
        
        return suggestions
    
    def set_saving_goal(self, goal_name: str, target_kwh: float, 
                       period: str = 'monthly', months: int = 1) -> Dict:
        """设置节能目标"""
        now = datetime.now()
        start_date = now.strftime('%Y-%m-%d')
        
        if period == 'monthly':
            if now.month == 12:
                end_date = f"{now.year+1}-01-01"
            else:
                end_date = f"{now.year}-{now.month+1:02d}-01"
        else:
            end_date = (now + timedelta(days=months*30)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO energy_saving_goals 
            (goal_name, target_kwh, target_cost, period, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (goal_name, target_kwh, target_kwh * self.electricity_rate, 
              period, start_date, end_date))
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'goal_id': goal_id,
            'goal_name': goal_name,
            'target_kwh': target_kwh,
            'target_cost': round(target_kwh * self.electricity_rate, 2),
            'period': f"{start_date} 至 {end_date}"
        }
    
    def get_goal_progress(self, goal_id: int = None) -> Dict:
        """获取节能目标进度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if goal_id:
            cursor.execute('''
                SELECT * FROM energy_saving_goals WHERE id = ? AND is_active = 1
            ''', (goal_id,))
        else:
            cursor.execute('''
                SELECT * FROM energy_saving_goals WHERE is_active = 1 ORDER BY id DESC LIMIT 1
            ''')
        
        goal = cursor.fetchone()
        
        if not goal:
            conn.close()
            return {'success': False, 'message': '无活跃节能目标'}
        
        goal_id, goal_name, target_kwh, target_cost, period, start_date, end_date, current_kwh, current_cost, is_active = goal
        
        # 计算当前进度
        cursor.execute('''
            SELECT SUM(energy_kwh), SUM(cost) FROM energy_records
            WHERE recorded_at >= ? AND recorded_at <= ?
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        current_kwh = result[0] or 0
        current_cost = result[1] or 0
        
        progress = (current_kwh / target_kwh * 100) if target_kwh > 0 else 0
        
        # 更新数据库
        cursor.execute('''
            UPDATE energy_saving_goals 
            SET current_kwh = ?, current_cost = ?
            WHERE id = ?
        ''', (current_kwh, current_cost, goal_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'goal_name': goal_name,
            'target_kwh': target_kwh,
            'target_cost': round(target_cost, 2),
            'current_kwh': round(current_kwh, 2),
            'current_cost': round(current_cost, 2),
            'progress': round(progress, 1),
            'period': f"{start_date} 至 {end_date}",
            'remaining_kwh': round(target_kwh - current_kwh, 2),
            'on_track': progress <= 100
        }


# 快捷函数
def quick_record(device_name: str, hours: float, power_watts: float = None):
    """快速记录用电"""
    service = EnergyManagementService()
    
    if power_watts is None:
        # 根据设备名自动匹配功率
        for key, power in service.device_power_reference.items():
            if key in device_name.lower():
                power_watts = power
                break
        if power_watts is None:
            power_watts = 100  # 默认 100W
    
    result = service.record_energy_usage(
        device_id=f"manual_{datetime.now().timestamp()}",
        device_name=device_name,
        power_watts=power_watts,
        usage_hours=hours
    )
    
    return result


if __name__ == "__main__":
    # 测试
    service = EnergyManagementService()
    
    # 记录一些测试数据
    logger.info("记录用电...")
    result = service.record_energy_usage(
        device_id="ac_001",
        device_name="客厅空调",
        power_watts=1500,
        usage_hours=8,
        room="客厅"
    )
    logger.info(f"记录结果：{result}")
    
    # 获取日报
    logger.info("\n今日用电报告:")
    report = service.get_daily_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 获取节能建议
    logger.info("\n节能建议:")
    suggestions = service.get_energy_saving_suggestions()
    for s in suggestions:
        logger.info(f"- {s['suggestion']}")
