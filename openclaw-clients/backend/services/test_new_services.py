#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增服务综合测试
测试：通知解析、自然语言记账、语音命令、场景自动化、个人数据、智能家居
"""

import unittest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ==================== 通知解析测试 ====================
class TestNotificationParser(unittest.TestCase):
    """通知解析服务测试"""
    
    def setUp(self):
        from notification_parser_service import NotificationParserService
        self.parser = NotificationParserService()
    
    def test_alipay_payment(self):
        """支付宝支付通知"""
        result = self.parser.parse('你通过扫码向美团外卖付款50.00元')
        self.assertEqual(result.get('type'), 'payment')
        if result.get('data'):
            self.assertIsNotNone(result['data'].get('amount'))
    
    def test_wechat_payment(self):
        """微信支付通知"""
        result = self.parser.parse('支付成功，向滴滴出行付款25.00元')
        self.assertEqual(result.get('type'), 'payment')
    
    def test_bank_payment(self):
        """银行卡消费通知"""
        result = self.parser.parse('您尾号1234的卡消费100.00元')
        self.assertEqual(result.get('type'), 'payment')
    
    def test_verification_code(self):
        """验证码提取"""
        result = self.parser.parse('您的验证码是：123456')
        self.assertEqual(result.get('type'), 'verification_code')
        if result.get('data'):
            self.assertEqual(result['data'].get('code'), '123456')
    
    def test_express_notification(self):
        """快递通知"""
        result = self.parser.parse('顺丰快递您的包裹已到达，单号SF12345678，取件码8888')
        self.assertEqual(result.get('type'), 'express')


# ==================== 自然语言记账测试 ====================
class TestNaturalLanguageAccounting(unittest.TestCase):
    """自然语言记账测试"""
    
    def setUp(self):
        from natural_language_accounting_service import parse_accounting_text
        self.parse = lambda text: asyncio.run(parse_accounting_text(text))
    
    def test_simple_expense(self):
        """简单支出"""
        result = self.parse('今天午饭花了50块')
        self.assertTrue(result.get('success'))
        self.assertEqual(result['data']['amount'], 50.0)
        self.assertEqual(result['data']['category'], '餐饮')
    
    def test_income(self):
        """收入"""
        result = self.parse('收工资5000')
        self.assertTrue(result.get('success'))
        self.assertEqual(result['data']['type'], 'income')
    
    def test_with_merchant(self):
        """带商户名"""
        result = self.parse('美团外卖花了38')
        self.assertTrue(result.get('success'))
        self.assertEqual(result['data']['merchant'], '美团')
    
    def test_transport(self):
        """交通支出"""
        result = self.parse('打车花了25元')
        self.assertTrue(result.get('success'))
        self.assertEqual(result['data']['category'], '交通')
    
    def test_time_expression(self):
        """时间表达"""
        result = self.parse('昨天晚餐120')
        self.assertTrue(result.get('success'))
        self.assertIn('date', result['data'])


# ==================== 语音命令测试 ====================
class TestVoiceCommand(unittest.TestCase):
    """语音命令测试"""
    
    def setUp(self):
        from voice_command_service import VoiceCommandService
        self.service = VoiceCommandService()
    
    def test_accounting_intent(self):
        """记账意图"""
        result = self.service.parse_command('记一笔50块午饭')
        self.assertEqual(result.get('intent'), 'accounting')
        self.assertEqual(result['slots']['amount'], 50.0)
    
    def test_query_intent(self):
        """查询意图"""
        result = self.service.parse_command('今天花了多少钱')
        self.assertEqual(result.get('intent'), 'query')
    
    def test_reminder_intent(self):
        """提醒意图"""
        result = self.service.parse_command('提醒我3点开会')
        self.assertEqual(result.get('intent'), 'reminder')
    
    def test_control_intent(self):
        """控制意图"""
        result = self.service.parse_command('打开客厅灯')
        self.assertEqual(result.get('intent'), 'control')
    
    def test_weather_intent(self):
        """天气意图"""
        result = self.service.parse_command('今天天气怎么样')
        self.assertEqual(result.get('intent'), 'weather')


# ==================== 场景自动化测试 ====================
class TestSceneAutomation(unittest.TestCase):
    """场景自动化测试"""
    
    def setUp(self):
        from scene_automation_service import SceneAutomationService
        self.service = SceneAutomationService(':memory:')
    
    def test_create_rule(self):
        """创建规则"""
        result = self.service.create_rule(
            name='回家模式',
            scene_type='home',
            trigger_type='location',
            trigger_config={'place_type': 'home'},
            actions=[{'type': 'device_control'}]
        )
        self.assertTrue(result.get('success'))
        self.assertIn('rule_id', result)
    
    def test_get_rules(self):
        """获取规则列表"""
        self.service.create_rule('测试', 'home', 'location', {}, [])
        rules = self.service.get_rules()
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
    
    def test_get_templates(self):
        """获取模板"""
        templates = self.service.get_templates()
        self.assertEqual(len(templates), 4)
    
    def test_trigger_scene(self):
        """触发场景"""
        self.service.create_rule('测试', 'home', 'location', {}, [{'type': 'test'}])
        result = self.service.trigger_scene('home')
        self.assertTrue(result.get('success'))
    
    def test_activate_deactivate(self):
        """激活/停用规则"""
        result = self.service.create_rule('测试', 'home', 'location', {}, [])
        rule_id = result['rule_id']
        
        # 停用
        result = self.service.deactivate_rule(rule_id)
        self.assertTrue(result.get('success'))
        
        # 激活
        result = self.service.activate_rule(rule_id)
        self.assertTrue(result.get('success'))


# ==================== 个人数据服务测试 ====================
class TestPersonalData(unittest.TestCase):
    """个人数据服务测试"""
    
    def setUp(self):
        from personal_data_service import PersonalDataService
        self.service = PersonalDataService(':memory:')
    
    def test_record_location(self):
        """记录位置"""
        result = self.service.record_location(39.9, 116.4)
        self.assertTrue(result.get('success'))
    
    def test_get_location_history(self):
        """获取位置历史"""
        self.service.record_location(39.9, 116.4)
        history = self.service.get_location_history()
        self.assertIsInstance(history, list)
    
    def test_record_health(self):
        """记录健康数据"""
        result = self.service.record_health(steps=5000, sleep_hours=7.5)
        self.assertTrue(result.get('success'))
    
    def test_get_health_summary(self):
        """获取健康摘要"""
        self.service.record_health(steps=5000)
        summary = self.service.get_health_summary()
        self.assertIn('today', summary)
    
    def test_record_payment(self):
        """记录支付"""
        result = self.service.record_payment(50, '美团外卖')
        self.assertTrue(result.get('success'))
        self.assertEqual(result['category'], '餐饮')
    
    def test_get_payment_summary(self):
        """获取支付摘要"""
        self.service.record_payment(50, '测试')
        summary = self.service.get_payment_summary()
        self.assertIn('total_expense', summary)


# ==================== 智能家居测试 ====================
class TestSmartHome(unittest.TestCase):
    """智能家居测试"""
    
    def test_discover_devices(self):
        """发现设备"""
        from smart_home_service import discover_devices
        result = asyncio.run(discover_devices())
        self.assertTrue(result.get('success'))
        self.assertIn('devices', result)
    
    def test_control_device(self):
        """控制设备"""
        from smart_home_service import control_device
        result = asyncio.run(control_device('test_light', 'turn_on'))
        self.assertIn('success', result)
    
    def test_get_device_status(self):
        """获取设备状态"""
        from smart_home_service import get_device_status
        result = asyncio.run(get_device_status('test_light'))
        self.assertIn('success', result)


# ==================== 增强提醒服务测试 ====================
class TestEnhancedReminder(unittest.TestCase):
    """增强提醒服务测试"""
    
    def setUp(self):
        from enhanced_reminder_service import EnhancedReminderService
        self.service = EnhancedReminderService(':memory:')
    
    def test_create_time_reminder(self):
        """创建定时提醒"""
        result = self.service.create_time_reminder(
            title='测试提醒',
            trigger_time='2025-03-20T10:00:00'
        )
        self.assertTrue(result.get('success'))
    
    def test_create_location_reminder(self):
        """创建位置提醒"""
        result = self.service.create_location_reminder(
            title='到家提醒',
            latitude=39.9,
            longitude=116.4
        )
        self.assertTrue(result.get('success'))
    
    def test_get_reminders(self):
        """获取提醒列表"""
        self.service.create_time_reminder('测试', '2025-03-20T10:00:00')
        reminders = self.service.get_reminders()
        self.assertIsInstance(reminders, list)
    
    def test_complete_reminder(self):
        """完成提醒"""
        result = self.service.create_time_reminder('测试', '2025-03-20T10:00:00')
        if result.get('success'):
            complete_result = self.service.complete(result['reminder_id'])
            self.assertTrue(complete_result.get('success'))


if __name__ == '__main__':
    unittest.main(verbosity=2)