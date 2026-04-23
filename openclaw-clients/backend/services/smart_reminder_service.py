import logging
logger = logging.getLogger(__name__)
"""
智能提醒服务
支持天气预警、预算预警、补货提醒、任务到期提醒等
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class SmartReminderService:
    """智能提醒服务"""
    
    def __init__(self):
        self.feishu_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/8c164cc1-e173-4011-a53c-75153147de7d"
        
        # 提醒配置
        self.reminder_config = {
            'weather_alert': True,      # 天气预警
            'budget_warning': True,     # 预算预警
            'restock_reminder': True,   # 补货提醒
            'task_reminder': True,      # 任务提醒
            'health_reminder': True,    # 健康提醒
        }
    
    def send_feishu_message(self, title: str, content: str, msg_type: str = "text"):
        """发送飞书消息"""
        if msg_type == "text":
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"**{title}**\n{content}"
                }
            }
        elif msg_type == "post":
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [
                                    {
                                        "tag": "text",
                                        "text": content
                                    }
                                ]
                            ]
                        }
                    }
                }
            }
        
        try:
            response = requests.post(self.feishu_webhook, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info(f"飞书消息发送成功：{title}")
                return True
        except Exception as e:
            logger.error(f"飞书消息发送失败：{e}")
        
        return False
    
    # ========== 天气预警 ==========
    
    def check_weather_alert(self, location: str = "北京") -> Optional[Dict]:
        """检查天气预警"""
        try:
            # 获取天气数据
            response = requests.get(f"http://wttr.in/{location}?format=j1", timeout=5)
            data = response.json()
            
            current = data['current_condition'][0]
            weather = current['weatherDesc'][0]['value']
            temp = int(current['temp_C'])
            wind = int(current['windspeedKmph'])
            humidity = int(current['humidity'])
            
            alerts = []
            
            # 高温预警
            if temp > 35:
                alerts.append(f"🌡️ 高温预警：当前{temp}℃，注意防暑降温")
            elif temp < -10:
                alerts.append(f"❄️ 低温预警：当前{temp}℃，注意保暖")
            
            # 大风预警
            if wind > 50:
                alerts.append(f"💨 大风预警：风力{wind}km/h，减少外出")
            
            # 高湿度预警
            if humidity > 80:
                alerts.append(f"💧 湿度过高：{humidity}%，注意除湿")
            
            # 恶劣天气
            if weather in ['Thunderstorm', 'Heavy rain', 'Snow', 'Fog']:
                alerts.append(f"⚠️ 恶劣天气：{weather}，注意出行安全")
            
            if alerts:
                alert_content = "\n".join(alerts)
                return {
                    'location': location,
                    'alerts': alerts,
                    'content': alert_content
                }
        
        except Exception as e:
            logger.error(f"天气预警检查失败：{e}")
        
        return None
    
    def send_weather_alert(self, location: str = "北京"):
        """发送天气预警"""
        alert = self.check_weather_alert(location)
        
        if alert:
            self.send_feishu_message(
                f"🌤️ {location}天气预警",
                alert['content']
            )
            return True
        
        return False
    
    # ========== 预算预警 ==========
    
    def check_budget_warning(self, family_service_url: str = "http://localhost:8082") -> List[Dict]:
        """检查预算预警"""
        warnings = []
        
        try:
            # 获取财务统计
            response = requests.get(f"{family_service_url}/api/finance/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json().get('stats', {})
                
                # 获取预算
                # 简化实现，实际应从 API 获取
                budgets = {
                    '餐饮': 2000,
                    '交通': 500,
                    '购物': 3000,
                    '娱乐': 1000
                }
                
                # 检查各分类预算
                for category, spent in stats.items():
                    budget = budgets.get(category, 0)
                    if budget > 0:
                        ratio = spent / budget
                        
                        if ratio >= 1.0:
                            warnings.append({
                                'category': category,
                                'budget': budget,
                                'spent': spent,
                                'ratio': ratio,
                                'level': 'critical',
                                'message': f"❌ {category} 已超支！花费¥{spent:.2f}，预算¥{budget:.2f}"
                            })
                        elif ratio >= 0.8:
                            warnings.append({
                                'category': category,
                                'budget': budget,
                                'spent': spent,
                                'ratio': ratio,
                                'level': 'warning',
                                'message': f"⚠️ {category} 预算紧张！已花{ratio*100:.0f}%，剩余¥{budget-spent:.2f}"
                            })
        
        except Exception as e:
            logger.error(f"预算预警检查失败：{e}")
        
        return warnings
    
    def send_budget_warning(self, family_service_url: str = "http://localhost:8082"):
        """发送预算预警"""
        warnings = self.check_budget_warning(family_service_url)
        
        if warnings:
            content = "\n".join([w['message'] for w in warnings])
            self.send_feishu_message("💰 预算预警", content)
            return True
        
        return False
    
    # ========== 补货提醒 ==========
    
    def check_restock_reminder(self, family_service_url: str = "http://localhost:8082") -> List[str]:
        """检查补货提醒"""
        suggestions = []
        
        try:
            response = requests.get(f"{family_service_url}/api/shopping/list", timeout=5)
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get('restock_suggestions', [])
        
        except Exception as e:
            logger.error(f"补货提醒检查失败：{e}")
        
        return suggestions
    
    def send_restock_reminder(self, family_service_url: str = "http://localhost:8082"):
        """发送补货提醒"""
        suggestions = self.check_restock_reminder(family_service_url)
        
        if suggestions:
            content = "以下商品可能需要补货：\n" + "\n".join(suggestions)
            self.send_feishu_message("🛒 补货提醒", content)
            return True
        
        return False
    
    # ========== 任务提醒 ==========
    
    def check_task_reminder(self, family_service_url: str = "http://localhost:8082") -> List[Dict]:
        """检查任务提醒"""
        reminders = []
        
        try:
            response = requests.get(f"{family_service_url}/api/tasks?status=pending", timeout=5)
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                
                now = datetime.now()
                
                for task in tasks:
                    due_date_str = task.get('due_date', '')
                    if due_date_str:
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                        days_left = (due_date - now).days
                        
                        if days_left < 0:
                            reminders.append({
                                'task': task['task_name'],
                                'assigned_to': task['assigned_to'],
                                'status': 'overdue',
                                'message': f"🔴 任务逾期：{task['task_name']}（负责人：{task['assigned_to']}）"
                            })
                        elif days_left == 0:
                            reminders.append({
                                'task': task['task_name'],
                                'assigned_to': task['assigned_to'],
                                'status': 'due_today',
                                'message': f"🟡 今日期限：{task['task_name']}（负责人：{task['assigned_to']}）"
                            })
                        elif days_left == 1:
                            reminders.append({
                                'task': task['task_name'],
                                'assigned_to': task['assigned_to'],
                                'status': 'due_tomorrow',
                                'message': f"🟠 明天到期：{task['task_name']}（负责人：{task['assigned_to']}）"
                            })
        
        except Exception as e:
            logger.error(f"任务提醒检查失败：{e}")
        
        return reminders
    
    def send_task_reminder(self, family_service_url: str = "http://localhost:8082"):
        """发送任务提醒"""
        reminders = self.check_task_reminder(family_service_url)
        
        if reminders:
            content = "\n".join([r['message'] for r in reminders])
            self.send_feishu_message("📋 任务提醒", content)
            return True
        
        return False
    
    # ========== 健康提醒 ==========
    
    def send_health_reminder(self, reminder_type: str = "water"):
        """发送健康提醒"""
        reminders = {
            'water': "💧 喝水提醒：该补充水分了，建议喝一杯水（250ml）",
            'stretch': "🧘 伸展提醒：久坐伤身，起来活动 5 分钟吧",
            'eye': "👁️ 护眼提醒：眼睛累了吗？看看远方，休息一下",
            'lunch': "🍱 午餐提醒：该吃午饭了，记得营养均衡",
            'sleep': "😴 睡眠提醒：时间不早了，早点休息吧"
        }
        
        content = reminders.get(reminder_type, "健康提醒")
        self.send_feishu_message("💚 健康提醒", content)
        return True
    
    # ========== 定时任务 ==========
    
    def run_scheduled_reminders(self):
        """运行定时提醒（简化实现）"""
        logger.info("开始运行定时提醒...")
        
        # 天气预警（每天早上 7 点）
        if self.reminder_config['weather_alert']:
            self.send_weather_alert("北京")
        
        # 预算预警（每天下午 6 点）
        if self.reminder_config['budget_warning']:
            self.send_budget_warning()
        
        # 补货提醒（每天晚上 8 点）
        if self.reminder_config['restock_reminder']:
            self.send_restock_reminder()
        
        # 任务提醒（每天早上 9 点）
        if self.reminder_config['task_reminder']:
            self.send_task_reminder()
        
        logger.info("定时提醒运行完成")


# 使用示例
if __name__ == '__main__':
    reminder = SmartReminderService()
    
    # 测试天气预警
    reminder.send_weather_alert("北京")
    
    # 测试预算预警
    reminder.send_budget_warning()
    
    # 测试健康提醒
    reminder.send_health_reminder('water')
