"""
场景自动化服务 - 简化版
支持回家/离家/睡眠/工作场景的自动化规则
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class SceneType(Enum):
    HOME = "home"
    AWAY = "away"
    SLEEP = "sleep"
    WORK = "work"


class TriggerType(Enum):
    LOCATION = "location"
    TIME = "time"
    EVENT = "event"


class SceneAutomationService:
    """场景自动化服务"""
    
    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        self._conn = None
        self._init_db()
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        c = self._get_conn().cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE,
                rule_name TEXT NOT NULL,
                scene_type TEXT,
                trigger_type TEXT NOT NULL,
                trigger_config TEXT,
                actions TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_triggered TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS scene_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                scene_type TEXT,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actions_executed TEXT
            )
        ''')
        
        self._conn.commit()
    
    # ========== 规则管理 ==========
    
    def create_rule(self, name: str, scene_type: str, trigger_type: str,
                   trigger_config: Dict, actions: List[Dict]) -> Dict[str, Any]:
        """创建自动化规则"""
        import uuid
        rule_id = str(uuid.uuid4())[:8]
        
        c = self._get_conn().cursor()
        c.execute('''
            INSERT INTO automation_rules 
            (rule_id, rule_name, scene_type, trigger_type, trigger_config, actions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (rule_id, name, scene_type, trigger_type, 
              json.dumps(trigger_config), json.dumps(actions)))
        
        self._conn.commit()
        
        return {
            'success': True,
            'rule_id': rule_id,
            'message': f'规则已创建：{name}'
        }
    
    def get_rules(self, active_only: bool = True) -> List[Dict]:
        """获取规则列表"""
        c = self._get_conn().cursor()
        
        if active_only:
            c.execute('SELECT * FROM automation_rules WHERE is_active = 1')
        else:
            c.execute('SELECT * FROM automation_rules')
        
        return [dict(row) for row in c.fetchall()]
    
    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """获取单个规则"""
        c = self._get_conn().cursor()
        c.execute('SELECT * FROM automation_rules WHERE rule_id = ?', (rule_id,))
        row = c.fetchone()
        return dict(row) if row else None
    
    def update_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]:
        """更新规则"""
        allowed_fields = ['rule_name', 'trigger_config', 'actions', 'is_active']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f'{field} = ?')
                values.append(json.dumps(kwargs[field]) if field in ['trigger_config', 'actions'] else kwargs[field])
        
        if not updates:
            return {'success': False, 'error': '没有有效更新字段'}
        
        values.append(rule_id)
        
        c = self._get_conn().cursor()
        c.execute(f'UPDATE automation_rules SET {", ".join(updates)} WHERE rule_id = ?', values)
        self._conn.commit()
        
        return {'success': True, 'message': '规则已更新'}
    
    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """删除规则"""
        c = self._get_conn().cursor()
        c.execute('DELETE FROM automation_rules WHERE rule_id = ?', (rule_id,))
        self._conn.commit()
        
        return {'success': True, 'message': '规则已删除'}
    
    def activate_rule(self, rule_id: str) -> Dict[str, Any]:
        """激活规则"""
        c = self._get_conn().cursor()
        c.execute('UPDATE automation_rules SET is_active = 1 WHERE rule_id = ?', (rule_id,))
        self._conn.commit()
        
        return {'success': True, 'message': '规则已激活'}
    
    def deactivate_rule(self, rule_id: str) -> Dict[str, Any]:
        """停用规则"""
        c = self._get_conn().cursor()
        c.execute('UPDATE automation_rules SET is_active = 0 WHERE rule_id = ?', (rule_id,))
        self._conn.commit()
        
        return {'success': True, 'message': '规则已停用'}
    
    # ========== 场景模板 ==========
    
    def get_templates(self) -> List[Dict]:
        """获取场景模板"""
        return [
            {
                'name': '回家模式',
                'scene_type': 'home',
                'trigger_type': 'location',
                'trigger_config': {'place_type': 'home'},
                'actions': [
                    {'type': 'device_control', 'device': 'living_room_light', 'action': 'turn_on'},
                    {'type': 'device_control', 'device': 'ac', 'action': 'set_temperature', 'value': 26},
                    {'type': 'notification', 'message': '欢迎回家！'}
                ]
            },
            {
                'name': '离家模式',
                'scene_type': 'away',
                'trigger_type': 'location',
                'trigger_config': {'place_type': 'home', 'trigger_on': 'leave'},
                'actions': [
                    {'type': 'device_control', 'device': 'all_lights', 'action': 'turn_off'},
                    {'type': 'device_control', 'device': 'ac', 'action': 'turn_off'},
                    {'type': 'notification', 'message': '已开启离家模式'}
                ]
            },
            {
                'name': '睡眠模式',
                'scene_type': 'sleep',
                'trigger_type': 'time',
                'trigger_config': {'time': '22:00'},
                'actions': [
                    {'type': 'device_control', 'device': 'all_lights', 'action': 'turn_off'},
                    {'type': 'device_control', 'device': 'phone', 'action': 'silent'},
                    {'type': 'notification', 'message': '晚安，好梦！'}
                ]
            },
            {
                'name': '工作模式',
                'scene_type': 'work',
                'trigger_type': 'location',
                'trigger_config': {'place_type': 'work'},
                'actions': [
                    {'type': 'device_control', 'device': 'phone', 'action': 'do_not_disturb'},
                    {'type': 'notification', 'message': '工作模式已开启'}
                ]
            }
        ]
    
    def create_from_template(self, template_name: str, custom_config: Dict = None) -> Dict[str, Any]:
        """从模板创建规则"""
        templates = self.get_templates()
        template = next((t for t in templates if t['name'] == template_name), None)
        
        if not template:
            return {'success': False, 'error': '模板不存在'}
        
        config = template['trigger_config']
        if custom_config:
            config.update(custom_config)
        
        return self.create_rule(
            name=template['name'],
            scene_type=template['scene_type'],
            trigger_type=template['trigger_type'],
            trigger_config=config,
            actions=template['actions']
        )
    
    # ========== 触发检测 ==========
    
    def check_location_trigger(self, latitude: float, longitude: float) -> List[Dict]:
        """检查位置触发"""
        c = self._get_conn().cursor()
        
        c.execute('''
            SELECT * FROM automation_rules 
            WHERE trigger_type = 'location' AND is_active = 1
        ''')
        
        triggered = []
        
        for row in c.fetchall():
            try:
                config = json.loads(row['trigger_config'])
                
                # 检查是否匹配位置类型
                place_type = config.get('place_type')
                trigger_on = config.get('trigger_on', 'enter')
                
                # 这里应该调用位置服务判断
                # 简化处理：根据配置判断
                should_trigger = False
                
                if place_type == 'home' and trigger_on == 'enter':
                    # 检测到家
                    should_trigger = True
                elif place_type == 'work':
                    should_trigger = True
                
                if should_trigger:
                    self._execute_actions(row['rule_id'], json.loads(row['actions']))
                    triggered.append({
                        'rule_id': row['rule_id'],
                        'rule_name': row['rule_name'],
                        'scene_type': row['scene_type']
                    })
            except Exception as e:
                continue
        
        return triggered
    
    def check_time_triggers(self) -> List[Dict]:
        """检查时间触发"""
        c = self._get_conn().cursor()
        
        c.execute('''
            SELECT * FROM automation_rules 
            WHERE trigger_type = 'time' AND is_active = 1
        ''')
        
        triggered = []
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        for row in c.fetchall():
            try:
                config = json.loads(row['trigger_config'])
                trigger_time = config.get('time')
                
                if trigger_time == current_time:
                    self._execute_actions(row['rule_id'], json.loads(row['actions']))
                    triggered.append({
                        'rule_id': row['rule_id'],
                        'rule_name': row['rule_name'],
                        'scene_type': row['scene_type']
                    })
            except:
                continue
        
        return triggered
    
    def _execute_actions(self, rule_id: str, actions: List[Dict]):
        """执行动作"""
        c = self._get_conn().cursor()
        
        # 记录执行历史
        c.execute('''
            INSERT INTO scene_history (rule_id, scene_type, actions_executed)
            SELECT ?, scene_type, ? FROM automation_rules WHERE rule_id = ?
        ''', (rule_id, json.dumps(actions), rule_id))
        
        # 更新最后触发时间
        c.execute('''
            UPDATE automation_rules SET last_triggered = ? WHERE rule_id = ?
        ''', (datetime.now().isoformat(), rule_id))
        
        self._conn.commit()
        
        # 返回动作列表供外部执行
        return actions
    
    def trigger_scene(self, scene_type: str) -> Dict[str, Any]:
        """手动触发场景"""
        c = self._get_conn().cursor()
        
        c.execute('''
            SELECT * FROM automation_rules 
            WHERE scene_type = ? AND is_active = 1
        ''', (scene_type,))
        
        rules = c.fetchall()
        all_actions = []
        
        for row in rules:
            actions = json.loads(row['actions'])
            self._execute_actions(row['rule_id'], actions)
            all_actions.extend(actions)
        
        return {
            'success': True,
            'scene_type': scene_type,
            'actions_count': len(all_actions),
            'actions': all_actions
        }


# 全局实例
_scene_service = None

def get_scene_service() -> SceneAutomationService:
    global _scene_service
    if _scene_service is None:
        _scene_service = SceneAutomationService()
    return _scene_service