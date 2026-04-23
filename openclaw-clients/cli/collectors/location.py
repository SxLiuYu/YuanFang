"""位置数据采集器"""

import random
import math
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional


class LocationCollector:
    """
    位置数据采集器
    
    在真实App中，这里会调用手机的GPS/网络定位API
    目前提供模拟数据用于测试
    """
    
    def __init__(self):
        self.current_location: Optional[Tuple[float, float]] = None
        self.history: List[Dict[str, Any]] = []
        
        # 已知位置（家、公司）
        self.known_places = {
            'home': (39.9042, 116.4074),      # 北京天安门附近（示例）
            'work': (39.9142, 116.4174),      # 公司位置（示例）
        }
        
        # 位置类型检测半径（米）
        self.detection_radius = 100
    
    def get_current_location(self) -> Dict[str, Any]:
        """
        获取当前位置
        
        Returns:
            位置数据
        """
        # 模拟GPS获取位置
        # 在真实App中调用: location.getLatitude(), location.getLongitude()
        
        if self.current_location:
            lat, lng = self.current_location
        else:
            # 随机生成一个位置（模拟）
            base_lat, base_lng = self.known_places['home']
            lat = base_lat + random.uniform(-0.01, 0.01)
            lng = base_lng + random.uniform(-0.01, 0.01)
        
        # 检测位置类型
        place_type = self._detect_place_type(lat, lng)
        
        location_data = {
            'latitude': lat,
            'longitude': lng,
            'accuracy': random.uniform(5, 50),
            'place_type': place_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self.history.append(location_data)
        return location_data
    
    def set_location(self, lat: float, lng: float) -> None:
        """设置当前位置（用于测试）"""
        self.current_location = (lat, lng)
    
    def set_place(self, place_name: str) -> None:
        """设置位置为已知地点"""
        if place_name in self.known_places:
            self.current_location = self.known_places[place_name]
    
    def _detect_place_type(self, lat: float, lng: float) -> str:
        """
        检测位置类型
        
        Args:
            lat: 纬度
            lng: 经度
        
        Returns:
            位置类型 (home/work/other)
        """
        for place_name, (place_lat, place_lng) in self.known_places.items():
            distance = self._calculate_distance(lat, lng, place_lat, place_lng)
            if distance <= self.detection_radius:
                return place_name
        
        return 'other'
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        计算两点间距离（米）
        
        使用Haversine公式
        """
        R = 6371000  # 地球半径（米）
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取位置历史"""
        return self.history[-limit:]
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """
        分析位置模式
        
        Returns:
            分析结果
        """
        if not self.history:
            return {'error': '没有位置历史数据'}
        
        # 统计各位置时间
        place_times = {'home': 0, 'work': 0, 'other': 0}
        
        for i, loc in enumerate(self.history[:-1]):
            next_loc = self.history[i + 1]
            time_diff = (datetime.fromisoformat(next_loc['timestamp']) - 
                        datetime.fromisoformat(loc['timestamp'])).total_seconds() / 3600
            place_times[loc['place_type']] += time_diff
        
        return {
            'home_hours': round(place_times['home'], 1),
            'work_hours': round(place_times['work'], 1),
            'other_hours': round(place_times['other'], 1),
            'total_records': len(self.history)
        }