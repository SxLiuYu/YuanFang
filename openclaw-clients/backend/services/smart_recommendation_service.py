import logging
logger = logging.getLogger(__name__)
"""
智能场景推荐服务
基于 AI 学习用户习惯，自动推荐自动化规则
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import sqlite3

class SmartSceneRecommendation:
    """智能场景推荐服务"""
    
    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        
        # 用户行为记录
        self.user_actions = []
        
        # 学习到的模式
        self.learned_patterns = []
        
        # 推荐阈值
        self.confidence_threshold = 0.7
    
    # ========== 行为学习 ==========
    
    def record_action(self, user_id: str, action_type: str, action_data: Dict, timestamp: datetime = None):
        """记录用户行为"""
        if timestamp is None:
            timestamp = datetime.now()
        
        action = {
            'user_id': user_id,
            'action_type': action_type,  # 'device_control', 'scene_activate', 'automation_create'
            'action_data': action_data,
            'timestamp': timestamp,
            'hour': timestamp.hour,
            'weekday': timestamp.weekday()
        }
        
        self.user_actions.append(action)
        
        # 保存到数据库
        self._save_action_to_db(action)
        
        # 分析模式
        self._analyze_patterns()
    
    def _save_action_to_db(self, action: Dict):
        """保存行为到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action_type TEXT,
                    action_data TEXT,
                    timestamp TIMESTAMP,
                    hour INTEGER,
                    weekday INTEGER
                )
            ''')
            
            c.execute('''
                INSERT INTO user_actions (user_id, action_type, action_data, timestamp, hour, weekday)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                action['user_id'],
                action['action_type'],
                json.dumps(action['action_data']),
                action['timestamp'].isoformat(),
                action['hour'],
                action['weekday']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存行为失败：{e}")
    
    def _load_actions_from_db(self, days: int = 30):
        """从数据库加载行为记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            c.execute('''
                SELECT user_id, action_type, action_data, timestamp, hour, weekday
                FROM user_actions
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (start_date.isoformat(),))
            
            rows = c.fetchall()
            conn.close()
            
            self.user_actions = [
                {
                    'user_id': row[0],
                    'action_type': row[1],
                    'action_data': json.loads(row[2]),
                    'timestamp': datetime.fromisoformat(row[3]),
                    'hour': row[4],
                    'weekday': row[5]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"加载行为失败：{e}")
    
    # ========== 模式分析 ==========
    
    def _analyze_patterns(self):
        """分析用户行为模式"""
        self.learned_patterns = []
        
        # 分析时间模式
        time_patterns = self._analyze_time_patterns()
        self.learned_patterns.extend(time_patterns)
        
        # 分析设备联动模式
        device_patterns = self._analyze_device_patterns()
        self.learned_patterns.extend(device_patterns)
        
        # 分析场景模式
        scene_patterns = self._analyze_scene_patterns()
        self.learned_patterns.extend(scene_patterns)
    
    def _analyze_time_patterns(self) -> List[Dict]:
        """分析时间模式"""
        patterns = []
        
        # 统计每个小时的行为
        hour_actions = defaultdict(list)
        for action in self.user_actions:
            hour_actions[action['hour']].append(action)
        
        # 找出频繁行为的小时
        for hour, actions in hour_actions.items():
            if len(actions) >= 5:  # 至少 5 次
                # 统计最常见的行为
                action_types = defaultdict(int)
                for action in actions:
                    action_types[action['action_type']] += 1
                
                most_common = max(action_types.items(), key=lambda x: x[1])
                
                pattern = {
                    'type': 'time',
                    'hour': hour,
                    'confidence': len(actions) / len(self.user_actions),
                    'suggestion': f"每天{hour}:00 自动执行{most_common[0]}"
                }
                
                if pattern['confidence'] >= self.confidence_threshold:
                    patterns.append(pattern)
        
        return patterns
    
    def _analyze_device_patterns(self) -> List[Dict]:
        """分析设备联动模式"""
        patterns = []
        
        # 统计设备控制序列
        device_sequences = defaultdict(int)
        
        # 按时间排序行为
        sorted_actions = sorted(self.user_actions, key=lambda x: x['timestamp'])
        
        # 分析连续操作（5 分钟内）
        for i in range(len(sorted_actions) - 1):
            action1 = sorted_actions[i]
            action2 = sorted_actions[i + 1]
            
            time_diff = (action2['timestamp'] - action1['timestamp']).total_seconds()
            
            if time_diff <= 300:  # 5 分钟内
                key = f"{action1['action_data']} -> {action2['action_data']}"
                device_sequences[key] += 1
        
        # 找出频繁的设备联动
        for sequence, count in device_sequences.items():
            if count >= 3:  # 至少 3 次
                pattern = {
                    'type': 'device_linkage',
                    'sequence': sequence,
                    'confidence': count / len(self.user_actions),
                    'suggestion': f"创建设备联动：{sequence}"
                }
                
                if pattern['confidence'] >= self.confidence_threshold:
                    patterns.append(pattern)
        
        return patterns
    
    def _analyze_scene_patterns(self) -> List[Dict]:
        """分析场景模式"""
        patterns = []
        
        # 统计场景使用频率
        scene_usage = defaultdict(int)
        
        for action in self.user_actions:
            if action['action_type'] == 'scene_activate':
                scene_name = action['action_data'].get('scene_name', '')
                scene_usage[scene_name] += 1
        
        # 找出常用场景
        for scene_name, count in scene_usage.items():
            if count >= 10:  # 至少 10 次
                pattern = {
                    'type': 'scene',
                    'scene_name': scene_name,
                    'confidence': count / len(self.user_actions),
                    'suggestion': f"场景'{scene_name}'使用频繁，建议添加到快捷方式"
                }
                
                if pattern['confidence'] >= self.confidence_threshold:
                    patterns.append(pattern)
        
        return patterns
    
    # ========== 智能推荐 ==========
    
    def get_recommendations(self, limit: int = 5) -> List[Dict]:
        """获取推荐列表"""
        # 重新加载数据
        self._load_actions_from_db()
        
        # 分析模式
        self._analyze_patterns()
        
        # 按置信度排序
        sorted_patterns = sorted(
            self.learned_patterns,
            key=lambda x: x['confidence'],
            reverse=True
        )
        
        return sorted_patterns[:limit]
    
    def get_morning_recommendations(self) -> List[Dict]:
        """获取晨间推荐"""
        morning_actions = [
            action for action in self.user_actions
            if 6 <= action['hour'] <= 9
        ]
        
        recommendations = []
        
        if morning_actions:
            # 分析晨间习惯
            recommendations.append({
                'type': 'morning_routine',
                'title': '晨间例行程序',
                'description': '检测到您每天早上 7-8 点使用设备',
                'suggestion': '建议创建晨间自动化：7:00 打开窗帘、播放新闻',
                'confidence': 0.85
            })
        
        return recommendations
    
    def get_evening_recommendations(self) -> List[Dict]:
        """获取晚间推荐"""
        evening_actions = [
            action for action in self.user_actions
            if 20 <= action['hour'] <= 23
        ]
        
        recommendations = []
        
        if evening_actions:
            recommendations.append({
                'type': 'evening_routine',
                'title': '晚安例行程序',
                'description': '检测到您每天晚上 10-11 点关闭设备',
                'suggestion': '建议创建晚安自动化：23:00 关闭所有灯、开启安防',
                'confidence': 0.80
            })
        
        return recommendations
    
    def get_energy_saving_recommendations(self) -> List[Dict]:
        """获取节能建议"""
        recommendations = []
        
        # 分析设备使用时长
        device_usage = defaultdict(int)
        for action in self.user_actions:
            if action['action_type'] == 'device_control':
                device_id = action['action_data'].get('device_id', '')
                device_usage[device_id] += 1
        
        # 找出长时间开启的设备
        for device_id, usage in device_usage.items():
            if usage > 20:  # 使用频繁
                recommendations.append({
                    'type': 'energy_saving',
                    'title': '节能建议',
                    'description': f'设备{device_id}使用频繁',
                    'suggestion': '建议设置定时关闭或添加运动传感器',
                    'confidence': 0.70
                })
        
        return recommendations
    
    # ========== 自动化规则生成 ==========
    
    def generate_automation_rule(self, pattern: Dict) -> Dict:
        """根据模式生成自动化规则"""
        if pattern['type'] == 'time':
            return {
                'name': f"定时任务 - {pattern['hour']}:00",
                'trigger': {
                    'type': 'time',
                    'value': f"{pattern['hour']:02d}:00"
                },
                'actions': [],  # 需要根据具体行为填充
                'confidence': pattern['confidence']
            }
        
        elif pattern['type'] == 'device_linkage':
            sequence = pattern['sequence'].split(' -> ')
            return {
                'name': f"设备联动 - {len(sequence)}个设备",
                'trigger': {
                    'type': 'device',
                    'device_id': sequence[0]
                },
                'actions': [
                    {'device_id': dev, 'action': 'auto'}
                    for dev in sequence[1:]
                ],
                'confidence': pattern['confidence']
            }
        
        return {}
    
    # ========== 反馈学习 ==========
    
    def accept_recommendation(self, recommendation_id: str):
        """用户接受推荐"""
        # 记录正面反馈
        logger.info(f"接受推荐：{recommendation_id}")
        # 可以增加类似推荐的权重
    
    def reject_recommendation(self, recommendation_id: str, reason: str = ''):
        """用户拒绝推荐"""
        # 记录负面反馈
        logger.info(f"拒绝推荐：{recommendation_id}, 原因：{reason}")
        # 可以减少类似推荐的权重
    
    def clear_learning_data(self, days: int = None):
        """清除学习数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if days:
                start_date = datetime.now() - timedelta(days=days)
                c.execute('DELETE FROM user_actions WHERE timestamp < ?', (start_date.isoformat(),))
            else:
                c.execute('DELETE FROM user_actions')
            
            conn.commit()
            conn.close()
            
            self.user_actions = []
            self.learned_patterns = []
            
            logger.info("清除学习数据完成")
        except Exception as e:
            logger.error(f"清除学习数据失败：{e}")


# 使用示例
if __name__ == '__main__':
    recommender = SmartSceneRecommendation()
    
    # 模拟用户行为
    now = datetime.now()
    for i in range(10):
        recommender.record_action(
            user_id='user_001',
            action_type='device_control',
            action_data={'device_id': 'light_1', 'action': 'on'},
            timestamp=now - timedelta(days=i, hours=1)
        )
    
    # 获取推荐
    recommendations = recommender.get_recommendations(limit=5)
    
    logger.info("\n智能推荐:")
    for rec in recommendations:
        logger.info(f"- {rec['suggestion']} (置信度：{rec['confidence']:.2f})")
    
    # 获取晨间推荐
    morning_recs = recommender.get_morning_recommendations()
    logger.info(f"\n晨间推荐：{len(morning_recs)}条")
    
    # 获取节能建议
    energy_recs = recommender.get_energy_saving_recommendations()
    logger.info(f"节能建议：{len(energy_recs)}条")
