"""健康数据采集器"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class HealthCollector:
    """
    健康数据采集器
    
    在真实App中，这里会调用:
    - Android: Google Fit API / Samsung Health API
    - iOS: HealthKit
    目前提供模拟数据用于测试
    """
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
    
    def get_today_health(self) -> Dict[str, Any]:
        """
        获取今日健康数据
        
        Returns:
            健康数据
        """
        # 模拟健康数据
        # 在真实App中调用健康API
        
        data = {
            'steps': random.randint(3000, 12000),
            'heart_rate': random.randint(60, 100),
            'sleep_hours': round(random.uniform(5, 9), 1),
            'calories': random.randint(1500, 3000),
            'active_minutes': random.randint(20, 90),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        }
        
        self.history.append(data)
        return data
    
    def get_health_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取历史健康数据
        
        Args:
            days: 天数
        
        Returns:
            历史数据列表
        """
        result = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            data = {
                'steps': random.randint(3000, 12000),
                'heart_rate': random.randint(60, 100),
                'sleep_hours': round(random.uniform(5, 9), 1),
                'calories': random.randint(1500, 3000),
                'date': date.strftime('%Y-%m-%d')
            }
            result.append(data)
        
        return result
    
    def analyze_trends(self) -> Dict[str, Any]:
        """
        分析健康趋势
        
        Returns:
            分析结果
        """
        if len(self.history) < 2:
            return {'error': '数据不足'}
        
        recent = self.history[-7:] if len(self.history) >= 7 else self.history
        
        avg_steps = sum(d['steps'] for d in recent) / len(recent)
        avg_sleep = sum(d['sleep_hours'] for d in recent) / len(recent)
        avg_heart_rate = sum(d['heart_rate'] for d in recent) / len(recent)
        
        return {
            'avg_steps': round(avg_steps),
            'avg_sleep': round(avg_sleep, 1),
            'avg_heart_rate': round(avg_heart_rate),
            'trend': 'improving' if avg_steps > 8000 else 'needs_attention',
            'recommendation': self._generate_recommendation(avg_steps, avg_sleep, avg_heart_rate)
        }
    
    def _generate_recommendation(self, avg_steps: float, avg_sleep: float, avg_hr: float) -> str:
        """生成健康建议"""
        recommendations = []
        
        if avg_steps < 5000:
            recommendations.append('建议增加每日步数，目标是8000步')
        if avg_sleep < 7:
            recommendations.append('睡眠时间偏少，建议保证7-8小时睡眠')
        if avg_hr > 90:
            recommendations.append('心率偏高，建议咨询医生')
        
        if not recommendations:
            return '健康状况良好，继续保持！'
        
        return '；'.join(recommendations)