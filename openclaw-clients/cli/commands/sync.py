"""同步命令模块"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional


def sync_location(client, lat: float, lng: float, accuracy: float = 10.0) -> Dict[str, Any]:
    """
    同步位置数据
    
    Args:
        client: OpenClaw客户端
        lat: 纬度
        lng: 经度
        accuracy: 精度(米)
    
    Returns:
        同步结果
    """
    try:
        response = client.post('/api/v1/personal/location', {
            'latitude': lat,
            'longitude': lng,
            'accuracy': accuracy,
            'timestamp': datetime.now().isoformat()
        })
        
        if response.get('success'):
            return {
                'success': True,
                'place_type': response.get('place_type', 'unknown'),
                'automations': response.get('automations', [])
            }
        return {'success': False, 'error': response.get('error', '同步失败')}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_health(client, steps: Optional[int] = None, heart_rate: Optional[int] = None,
                sleep: Optional[float] = None, calories: Optional[int] = None) -> Dict[str, Any]:
    """
    同步健康数据
    
    Args:
        client: OpenClaw客户端
        steps: 步数
        heart_rate: 心率
        sleep: 睡眠时长
        calories: 卡路里
    
    Returns:
        同步结果
    """
    try:
        data = {'timestamp': datetime.now().isoformat()}
        
        if steps is not None:
            data['steps'] = steps
        if heart_rate is not None:
            data['heart_rate'] = heart_rate
        if sleep is not None:
            data['sleep_hours'] = sleep
        if calories is not None:
            data['calories'] = calories
        
        response = client.post('/api/v1/health/metrics/record', data)
        
        if response.get('success'):
            return {
                'success': True,
                'advice': response.get('advice')
            }
        return {'success': False, 'error': response.get('error', '同步失败')}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_payment(client, amount: float, merchant: str, category: Optional[str] = None,
                 payment_type: str = 'expense') -> Dict[str, Any]:
    """
    同步支付数据(自动记账)
    
    Args:
        client: OpenClaw客户端
        amount: 金额
        merchant: 商户
        category: 分类
        payment_type: 类型(expense/income)
    
    Returns:
        同步结果
    """
    try:
        # 商户名称自动分类
        if not category:
            category = auto_categorize(merchant)
        
        response = client.post('/api/v1/finance/transaction/add', {
            'amount': amount,
            'category': category,
            'type': payment_type,
            'description': merchant,
            'source': 'mobile_sync'
        })
        
        if response.get('success'):
            return {
                'success': True,
                'transaction_id': response.get('transaction_id'),
                'category': category,
                'budget_warning': response.get('budget_warning')
            }
        return {'success': False, 'error': response.get('error', '同步失败')}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_calendar(client, title: str, date: str, time: Optional[str] = None,
                  location: Optional[str] = None) -> Dict[str, Any]:
    """
    同步日程数据
    
    Args:
        client: OpenClaw客户端
        title: 事件标题
        date: 日期
        time: 时间
        location: 地点
    
    Returns:
        同步结果
    """
    try:
        start_time = date
        if time:
            start_time = f"{date}T{time}:00"
        
        response = client.post('/api/v1/calendar/event/create', {
            'title': title,
            'start_time': start_time,
            'location': location,
            'source': 'mobile_sync'
        })
        
        if response.get('success'):
            return {'success': True, 'event_id': response.get('event_id')}
        return {'success': False, 'error': response.get('error', '同步失败')}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def auto_categorize(merchant: str) -> str:
    """
    根据商户名称自动分类
    
    Args:
        merchant: 商户名称
    
    Returns:
        分类
    """
    merchant_lower = merchant.lower()
    
    categories = {
        '餐饮': ['美团', '饿了么', '外卖', '餐厅', '肯德基', '麦当劳', '星巴克', '奶茶', '咖啡'],
        '交通': ['滴滴', '打车', '地铁', '公交', '加油', '停车', '高速'],
        '购物': ['淘宝', '京东', '拼多多', '超市', '便利店', '商场'],
        '娱乐': ['电影', '游戏', '音乐', '视频', '会员'],
        '通讯': ['移动', '联通', '电信', '话费'],
        '水电': ['水费', '电费', '燃气', '物业'],
        '医疗': ['医院', '药店', '诊所', '体检'],
        '教育': ['书店', '培训', '课程', '学习'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in merchant_lower:
                return category
    
    return '其他'