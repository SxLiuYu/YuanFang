"""个人数据模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LocationData(BaseModel):
    """位置数据模型"""
    latitude: float
    longitude: float
    accuracy: float = 10.0
    place_type: str = "other"
    timestamp: str = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)


class HealthData(BaseModel):
    """健康数据模型"""
    steps: Optional[int] = None
    heart_rate: Optional[int] = None
    sleep_hours: Optional[float] = None
    calories: Optional[int] = None
    active_minutes: Optional[int] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)


class PaymentData(BaseModel):
    """支付数据模型"""
    amount: float
    merchant: str
    category: Optional[str] = None
    payment_type: str = "expense"
    platform: Optional[str] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)