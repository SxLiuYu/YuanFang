import logging
logger = logging.getLogger(__name__)
"""
家庭自动化规则引擎
支持条件触发、定时任务、场景联动等自动化功能
"""

import json
from datetime import datetime, time
from typing import Dict, List, Optional, Callable
import threading
import time as time_module

class AutomationRule:
    """自动化规则"""
    
    def __init__(self, rule_id: str, name: str, description: str = ""):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.enabled = True
        
        # 触发条件
        self.triggers = []  # [{'type': 'time', 'value': '07:00'}, {'type': 'device', 'device_id': 'xxx', 'state': 'on'}]
        
        # 执行动作
        self.actions = []  # [{'type': 'control', 'device_id': 'xxx', 'action': 'on'}]
        
        # 条件（可选）
        self.conditions = []  # [{'type': 'weather', 'condition': 'rainy'}]
    
    def check_triggers(self, context: Dict) -> bool:
        """检查触发条件是否满足"""
        if not self.enabled:
            return False
        
        for trigger in self.triggers:
            if not self._check_trigger(trigger, context):
                return False
        
        return True
    
    def _check_trigger(self, trigger: Dict, context: Dict) -> bool:
        """检查单个触发条件"""
        trigger_type = trigger.get('type')
        
        if trigger_type == 'time':
            # 时间触发
            trigger_time = trigger.get('value')  # '07:00'
            current_time = datetime.now().strftime('%H:%M')
            return current_time == trigger_time
        
        elif trigger_type == 'device':
            # 设备状态触发
            device_id = trigger.get('device_id')
            expected_state = trigger.get('state')
            actual_state = context.get('devices', {}).get(device_id, {}).get('state')
            return actual_state == expected_state
        
        elif trigger_type == 'weather':
            # 天气触发
            expected_weather = trigger.get('weather')
            actual_weather = context.get('weather', {})
            return actual_weather.get('condition') == expected_weather
        
        return False
    
    def execute_actions(self, action_executor: Callable):
        """执行动作"""
        if not self.enabled:
            return
        
        for action in self.actions:
            try:
                action_executor(action)
            except Exception as e:
                logger.error(f"执行动作失败：{action} - {e}")
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'triggers': self.triggers,
            'actions': self.actions,
            'conditions': self.conditions
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'AutomationRule':
        """从字典创建"""
        rule = AutomationRule(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data.get('description', '')
        )
        rule.enabled = data.get('enabled', True)
        rule.triggers = data.get('triggers', [])
        rule.actions = data.get('actions', [])
        rule.conditions = data.get('conditions', [])
        return rule


class AutomationEngine:
    """自动化引擎"""
    
    def __init__(self):
        self.rules: Dict[str, AutomationRule] = {}
        self.running = False
        self.context = {}
        
        # 动作执行器
        self.action_executor = None
    
    def add_rule(self, rule: AutomationRule):
        """添加规则"""
        self.rules[rule.rule_id] = rule
        logger.info(f"添加自动化规则：{rule.name}")
    
    def remove_rule(self, rule_id: str):
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除自动化规则：{rule_id}")
    
    def enable_rule(self, rule_id: str):
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def set_action_executor(self, executor: Callable):
        """设置动作执行器"""
        self.action_executor = executor
    
    def update_context(self, context: Dict):
        """更新上下文"""
        self.context.update(context)
    
    def start(self):
        """启动自动化引擎"""
        self.running = True
        
        # 启动检查线程
        thread = threading.Thread(target=self._check_rules_loop, daemon=True)
        thread.start()
        logger.info("自动化引擎已启动")
    
    def stop(self):
        """停止自动化引擎"""
        self.running = False
        logger.info("自动化引擎已停止")
    
    def _check_rules_loop(self):
        """循环检查规则"""
        while self.running:
            try:
                self._check_all_rules()
            except Exception as e:
                logger.error(f"检查规则失败：{e}")
            
            # 每分钟检查一次
            time_module.sleep(60)
    
    def _check_all_rules(self):
        """检查所有规则"""
        for rule in self.rules.values():
            if rule.check_triggers(self.context):
                logger.info(f"触发规则：{rule.name}")
                rule.execute_actions(self.action_executor)
    
    # ========== 预设规则 ==========
    
    def create_morning_routine(self):
        """创建晨间例行程序"""
        rule = AutomationRule("morning_routine", "晨间例行程序", "每天早上 7 点执行")
        
        rule.triggers = [
            {'type': 'time', 'value': '07:00'}
        ]
        
        rule.actions = [
            {'type': 'control', 'device_id': 'light_living', 'action': 'on'},
            {'type': 'control', 'device_id': 'curtain_living', 'action': 'open'},
            {'type': 'notify', 'message': '早上好！新的一天开始了'},
        ]
        
        self.add_rule(rule)
    
    def create_goodnight_routine(self):
        """创建晚安例行程序"""
        rule = AutomationRule("goodnight_routine", "晚安例行程序", "每天晚上 11 点执行")
        
        rule.triggers = [
            {'type': 'time', 'value': '23:00'}
        ]
        
        rule.actions = [
            {'type': 'control', 'device_id': 'light_all', 'action': 'off'},
            {'type': 'control', 'device_id': 'ac_all', 'action': 'off'},
            {'type': 'arm_security', 'mode': 'night'},
            {'type': 'notify', 'message': '晚安，祝你好梦'},
        ]
        
        self.add_rule(rule)
    
    def create_leave_home_routine(self):
        """创建离家例行程序"""
        rule = AutomationRule("leave_home", "离家模式", "所有灯关闭时自动开启安防")
        
        rule.triggers = [
            {'type': 'device', 'device_id': 'light_all', 'state': 'off'}
        ]
        
        rule.actions = [
            {'type': 'arm_security', 'mode': 'away'},
            {'type': 'control', 'device_id': 'camera_all', 'action': 'start_recording'},
        ]
        
        self.add_rule(rule)
    
    def create_rain_routine(self):
        """创建雨天例行程序"""
        rule = AutomationRule("rain_routine", "雨天自动关窗", "下雨时自动关闭窗户")
        
        rule.triggers = [
            {'type': 'weather', 'weather': 'rainy'}
        ]
        
        rule.actions = [
            {'type': 'control', 'device_id': 'window_all', 'action': 'close'},
            {'type': 'notify', 'message': '正在下雨，已自动关闭窗户'},
        ]
        
        self.add_rule(rule)
    
    def create_budget_alert_routine(self):
        """创建预算预警例行程序"""
        rule = AutomationRule("budget_alert", "预算预警", "每天下午 6 点检查预算")
        
        rule.triggers = [
            {'type': 'time', 'value': '18:00'}
        ]
        
        rule.actions = [
            {'type': 'api', 'url': 'http://localhost:8082/api/finance/budget/check'},
        ]
        
        self.add_rule(rule)


# 使用示例
if __name__ == '__main__':
    engine = AutomationEngine()
    
    # 设置动作执行器（简化实现）
    def execute_action(action):
        logger.info(f"执行动作：{action}")
    
    engine.set_action_executor(execute_action)
    
    # 创建预设规则
    engine.create_morning_routine()
    engine.create_goodnight_routine()
    engine.create_leave_home_routine()
    
    # 启动引擎
    engine.start()
    
    # 保持运行
    try:
        while True:
            time_module.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
