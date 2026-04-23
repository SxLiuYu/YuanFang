# -*- coding: utf-8 -*-
"""
OpenClaw 设备同步服务 - 阿里云函数计算
功能：设备注册、心跳上报、设备列表查询
"""

import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

# 配置 (从环境变量读取)
ACCESS_KEY_ID = "你的 AccessKey ID"
ACCESS_KEY_SECRET = "你的 AccessKey Secret"
REGION_ID = "cn-beijing"  # 根据实际区域修改
TABLESTORE_ENDPOINT = "https://你的实例.cn-beijing.ots.aliyuncs.com"
TABLESTORE_INSTANCE_NAME = "你的实例名"
TABLESTORE_TABLE_NAME = "devices"

# 在线状态阈值 (秒)
ONLINE_THRESHOLD = 120  # 2 分钟内在线


def handler(environ, start_response):
    """函数计算入口"""
    try:
        request_body = environ.get('wsgi.input', '').read()
        if request_body:
            data = json.loads(request_body)
        else:
            data = {}
        
        action = environ.get('PATH_INFO', '').split('/')[-1]
        method = environ.get('REQUEST_METHOD', 'GET')
        
        # 路由处理
        if action == 'register' and method == 'POST':
            result = register_device(data)
        elif action == 'heartbeat' and method == 'POST':
            result = update_heartbeat(data)
        elif action == 'list' and method == 'GET':
            result = get_device_list(data)
        elif action == 'login' and method == 'POST':
            result = login_user(data)
        elif action == 'register_user' and method == 'POST':
            result = register_user(data)
        else:
            result = {'success': False, 'error': 'Unknown action'}
        
        # 返回响应
        status = '200 OK'
        response_headers = [
            ('Content-type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type')
        ]
        start_response(status, response_headers)
        return [json.dumps(result).encode('utf-8')]
        
    except Exception as e:
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'application/json')]
        start_response(status, response_headers)
        return [json.dumps({'success': False, 'error': str(e)}).encode('utf-8')]


def register_device(data):
    """注册设备"""
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    device_model = data.get('device_model')
    user_id = data.get('user_id')
    app_version = data.get('app_version', '1.0')
    os_version = data.get('os_version', '')
    
    if not all([device_id, user_id]):
        return {'success': False, 'error': 'Missing required fields'}
    
    try:
        # 使用 TableStore SDK 插入/更新设备
        from tablestore import OTSClient, RowExistenceExpectation, PutRowRequest, Row
        
        client = OTSClient(TABLESTORE_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET, TABLESTORE_INSTANCE_NAME)
        
        # 主键
        primary_key = [('device_id', device_id)]
        
        # 属性列
        attribute_columns = [
            ('device_name', device_name),
            ('device_model', device_model),
            ('user_id', user_id),
            ('app_version', app_version),
            ('os_version', os_version),
            ('status', 'online'),
            ('last_seen', int(time.time())),
            ('battery', data.get('battery', -1)),
            ('created_at', int(time.time()))
        ]
        
        row = Row(primary_key, attribute_columns)
        request = PutRowRequest(TABLESTORE_TABLE_NAME, row, RowExistenceExpectation.IGNORE)
        client.put_row(request)
        
        return {'success': True, 'message': 'Device registered'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_heartbeat(data):
    """更新心跳"""
    device_id = data.get('device_id')
    battery = data.get('battery', -1)
    
    if not device_id:
        return {'success': False, 'error': 'Missing device_id'}
    
    try:
        from tablestore import OTSClient, UpdateRowRequest, Row, UpdateRowResponse
        
        client = OTSClient(TABLESTORE_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET, TABLESTORE_INSTANCE_NAME)
        
        # 主键
        primary_key = [('device_id', device_id)]
        
        # 更新列
        update_of_attribute_columns = [
            ('status', 'online'),
            ('last_seen', int(time.time())),
            ('battery', battery)
        ]
        
        row = Row(primary_key, update_of_attribute_columns)
        request = UpdateRowRequest(TABLESTORE_TABLE_NAME, row)
        client.update_row(request)
        
        return {'success': True, 'message': 'Heartbeat updated'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_device_list(data):
    """获取设备列表"""
    user_id = data.get('user_id')
    
    if not user_id:
        return {'success': False, 'error': 'Missing user_id'}
    
    try:
        from tablestore import OTSClient, GetRangeRequest, Direction, RangeRowQueryCriteria
        
        client = OTSClient(TABLESTORE_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET, TABLESTORE_INSTANCE_NAME)
        
        # 查询用户的所有设备
        start_primary_key = [('device_id', None)]  # 从头开始
        end_primary_key = [('device_id', None)]    # 到尾结束
        
        # 过滤条件：user_id 匹配
        from tablestore import SingleColumnCondition, ComparatorType
        cond = SingleColumnCondition('user_id', user_id, ComparatorType.EQUAL)
        
        criteria = RangeRowQueryCriteria(TABLESTORE_TABLE_NAME, start_primary_key, end_primary_key, limit=100, condition=cond)
        request = GetRangeRequest(criteria)
        response = client.get_range(request)
        
        devices = []
        current_time = int(time.time())
        
        for row in response.rows:
            device = {}
            for col in row[1]:
                if col[0] == 'device_id':
                    device['device_id'] = col[1]
                elif col[0] == 'device_name':
                    device['device_name'] = col[1]
                elif col[0] == 'device_model':
                    device['device_model'] = col[1]
                elif col[0] == 'status':
                    device['status'] = col[1]
                elif col[0] == 'battery':
                    device['battery'] = col[1]
                elif col[0] == 'last_seen':
                    last_seen = col[1]
                    device['last_seen'] = last_seen
                    # 计算在线状态
                    diff = current_time - last_seen
                    if diff < ONLINE_THRESHOLD:
                        device['status'] = 'online'
                        device['last_seen_text'] = '刚刚'
                    elif diff < 3600:
                        device['status'] = 'offline'
                        device['last_seen_text'] = f'{diff // 60}分钟前'
                    elif diff < 86400:
                        device['status'] = 'offline'
                        device['last_seen_text'] = f'{diff // 3600}小时前'
                    else:
                        device['status'] = 'offline'
                        device['last_seen_text'] = f'{diff // 86400}天前'
            
            if device:
                devices.append(device)
        
        return {'success': True, 'devices': devices}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def login_user(data):
    """用户登录 (简化版，实际应使用阿里云用户认证)"""
    username = data.get('username')
    # 简化：用户名即 user_id
    if username:
        return {'success': True, 'user_id': f'user_{username}', 'session_token': 'mock_token'}
    return {'success': False, 'error': 'Invalid credentials'}


def register_user(data):
    """用户注册 (简化版)"""
    username = data.get('username')
    if username:
        return {'success': True, 'user_id': f'user_{username}', 'session_token': 'mock_token'}
    return {'success': False, 'error': 'Invalid username'}
