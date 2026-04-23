"""
家庭服务 API 单元测试
"""

import unittest
import json
from family_services_api import app, init_db

class TestFamilyServicesAPI(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        init_db()
    
    def test_get_devices(self):
        """测试获取设备列表"""
        response = self.client.get('/api/smarthome/devices')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('devices', data)
    
    def test_add_device(self):
        """测试添加设备"""
        device_data = {
            'device_id': 'TEST_001',
            'device_name': '测试灯',
            'device_type': 'light',
            'platform': 'test',
            'room': '测试房间'
        }
        
        response = self.client.post(
            '/api/smarthome/device',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_control_device(self):
        """测试控制设备"""
        control_data = {
            'device_id': 'TEST_001',
            'action': 'on'
        }
        
        response = self.client.post(
            '/api/smarthome/control',
            data=json.dumps(control_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_add_transaction(self):
        """测试添加交易记录"""
        transaction_data = {
            'amount': 50.0,
            'type': 'expense',
            'category': '餐饮',
            'recorded_by': '测试用户'
        }
        
        response = self.client.post(
            '/api/finance/transaction',
            data=json.dumps(transaction_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_get_finance_stats(self):
        """测试获取财务统计"""
        response = self.client.get('/api/finance/stats?period=monthly')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('stats', data)
        self.assertIn('period', data)
    
    def test_set_budget(self):
        """测试设置预算"""
        budget_data = {
            'category': '餐饮',
            'amount': 1500.0,
            'period': 'monthly'
        }
        
        response = self.client.post(
            '/api/finance/budget',
            data=json.dumps(budget_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_get_tasks(self):
        """测试获取任务列表"""
        response = self.client.get('/api/tasks?status=pending')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('tasks', data)
    
    def test_create_task(self):
        """测试创建任务"""
        task_data = {
            'task_name': '测试任务',
            'description': '测试描述',
            'assigned_to': '测试用户',
            'points': 10
        }
        
        response = self.client.post(
            '/api/tasks',
            data=json.dumps(task_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_get_leaderboard(self):
        """测试获取排行榜"""
        response = self.client.get('/api/leaderboard')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('leaderboard', data)
    
    def test_get_shopping_list(self):
        """测试获取购物清单"""
        response = self.client.get('/api/shopping/list')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('items', data)
    
    def test_add_shopping_item(self):
        """测试添加购物项"""
        item_data = {
            'item_name': '测试商品',
            'category': '食品',
            'quantity': 2,
            'unit': '个'
        }
        
        response = self.client.post(
            '/api/shopping/item',
            data=json.dumps(item_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_price_compare(self):
        """测试价格对比"""
        response = self.client.get('/api/shopping/compare?item_name=测试商品')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('prices', data)
        self.assertIn('item', data)

if __name__ == '__main__':
    unittest.main()
