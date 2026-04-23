#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw - 语音增强服务
支持设备控制、场景控制、智能建议、自然语言日程解析

Author: 于金泽
Version: 1.0.0
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from collections import defaultdict
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

class VoiceCommandRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None

class VoiceCommandResponse(BaseModel):
    success: bool
    intent: str
    slots: Dict[str, Any]
    action: Optional[Dict[str, Any]] = None
    message: str
    suggestions: List[Dict[str, Any]] = []

class VoiceSuggestion(BaseModel):
    type: str
    title: str
    description: str
    confidence: float
    action: Dict[str, Any]
    icon: Optional[str] = None

class ScheduleParseRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class ScheduleParseResponse(BaseModel):
    success: bool
    title: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recurrence: Optional[str] = None
    reminders: List[datetime] = []
    confidence: float

# ═══════════════════════════════════════════════════════════════
# 语音增强服务类
# ═══════════════════════════════════════════════════════════════

class VoiceEnhancedService:
    """语音增强服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent.parent / "data" / "voice_enhanced.db")
        self._init_database()
        
        # 设备控制命令模式
        self.device_control_patterns = {
            "turn_on": [
                r"打开(.+)",
                r"开启(.+)",
                r"启动(.+)",
                r"开(.+)"
            ],
            "turn_off": [
                r"关闭(.+)",
                r"关掉(.+)",
                r"停止(.+)",
                r"关(.+)"
            ],
            "adjust": [
                r"把(.+)(调|设置)(到|为)(.+)",
                r"(.+)(调|设置)(到|为)(.+)",
                r"调(高|低)(.+)(.+)"
            ],
            "query": [
                r"查询(.+)状态",
                r"(.+)是(什么|多少)",
                r"看看(.+)"
            ]
        }
        
        # 场景控制命令模式
        self.scene_control_patterns = {
            "home": [
                r"我(回)?家了",
                r"到家了",
                r"回家模式"
            ],
            "leave": [
                r"我(出)?门了",
                r"离开家",
                r"离家模式"
            ],
            "sleep": [
                r"我要睡觉(了)?",
                r"睡觉模式",
                r"晚安"
            ],
            "work": [
                r"我要工作(了)?",
                r"工作模式",
                r"开始工作"
            ]
        }
        
        # 时间解析模式
        self.time_patterns = {
            "absolute": [
                (r"(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})点(\d{1,2})分", "%Y年%m月%d日%H点%M分"),
                (r"(\d{1,2})月(\d{1,2})日(\d{1,2})点(\d{1,2})分", "%m月%d日%H点%M分"),
                (r"(\d{1,2})月(\d{1,2})日(\d{1,2})点", "%m月%d日%H点"),
                (r"(\d{1,2})点(\d{1,2})分", "%H点%M分"),
                (r"(\d{1,2})点", "%H点")
            ],
            "relative": [
                (r"明天", timedelta(days=1)),
                (r"后天", timedelta(days=2)),
                (r"大后天", timedelta(days=3)),
                (r"下周(.+)", None),  # 需要特殊处理
                (r"(\d+)小时后", "hours"),
                (r"(\d+)分钟后", "minutes"),
                (r"(\d+)天后", "days")
            ],
            "recurrence": [
                (r"每天", "daily"),
                (r"每周(.+)", "weekly"),
                (r"每月(.+)", "monthly"),
                (r"每个工作日", "workday")
            ]
        }
        
        # 智能建议权重
        self.suggestion_weights = {
            "time": 0.3,      # 基于时间
            "habit": 0.4,     # 基于习惯
            "context": 0.2,   # 基于上下文
            "popularity": 0.1 # 基于流行度
        }
    
    def _init_database(self):
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户行为记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_behaviors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            )
        """)
        
        # 设备使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                action TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                time_slot TEXT,
                UNIQUE(device_id, action, time_slot)
            )
        """)
        
        # 建议模板表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestion_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                condition TEXT,
                action TEXT,
                priority INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 设备控制
    # ═══════════════════════════════════════════════════════════════
    
    async def parse_device_control(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析设备控制命令"""
        text = text.strip()
        
        # 尝试匹配各种控制模式
        for action, patterns in self.device_control_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    slots = {"action": action}
                    
                    if action == "turn_on":
                        slots["device"] = match.group(1).strip()
                    elif action == "turn_off":
                        slots["device"] = match.group(1).strip()
                    elif action == "adjust":
                        groups = match.groups()
                        slots["device"] = groups[0].strip()
                        if "高" in text or "低" in text:
                            slots["direction"] = "up" if "高" in text else "down"
                            slots["attribute"] = groups[2] if len(groups) > 2 else "temperature"
                        else:
                            slots["value"] = groups[-1] if groups[-1] else ""
                    elif action == "query":
                        slots["device"] = match.group(1).strip()
                    
                    return "device_control", slots
        
        return "unknown", {}
    
    async def execute_device_control(self, text: str, context: Dict[str, Any] = None) -> VoiceCommandResponse:
        """执行设备控制命令"""
        intent, slots = await self.parse_device_control(text)
        
        if intent == "unknown":
            return VoiceCommandResponse(
                success=False,
                intent=intent,
                slots=slots,
                message="抱歉，我无法理解您的设备控制命令"
            )
        
        # 记录用户行为
        await self._record_behavior(
            user_id=context.get("user_id", "default"),
            action_type="device_control",
            action_data={"text": text, "slots": slots}
        )
        
        # 更新设备使用统计
        if "device" in slots:
            await self._update_device_stats(
                device_id=slots["device"],
                action=slots["action"]
            )
        
        # 构建执行动作
        action = {
            "type": "device_control",
            "device": slots.get("device"),
            "action": slots.get("action"),
            "params": {k: v for k, v in slots.items() if k not in ["device", "action"]}
        }
        
        # 生成建议
        suggestions = await self._generate_suggestions_after_action(
            action_type="device_control",
            device=slots.get("device"),
            user_id=context.get("user_id", "default") if context else "default"
        )
        
        # 生成响应消息
        message = self._generate_device_response(slots)
        
        return VoiceCommandResponse(
            success=True,
            intent=intent,
            slots=slots,
            action=action,
            message=message,
            suggestions=[s.dict() for s in suggestions]
        )
    
    def _generate_device_response(self, slots: Dict[str, Any]) -> str:
        """生成设备控制响应消息"""
        device = slots.get("device", "设备")
        action = slots.get("action")
        
        if action == "turn_on":
            return f"好的，已为您打开{device}"
        elif action == "turn_off":
            return f"好的，已为您关闭{device}"
        elif action == "adjust":
            direction = slots.get("direction")
            value = slots.get("value")
            if direction:
                dir_text = "调高" if direction == "up" else "调低"
                return f"好的，已为您将{device}{dir_text}"
            elif value:
                return f"好的，已将{device}调整到{value}"
        elif action == "query":
            return f"正在查询{device}状态..."
        
        return f"已执行{device}控制命令"
    
    # ═══════════════════════════════════════════════════════════════
    # 场景控制
    # ═══════════════════════════════════════════════════════════════
    
    async def parse_scene_control(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析场景控制命令"""
        text = text.strip()
        
        for scene, patterns in self.scene_control_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return "scene_control", {"scene": scene}
        
        return "unknown", {}
    
    async def execute_scene_control(self, text: str, context: Dict[str, Any] = None) -> VoiceCommandResponse:
        """执行场景控制命令"""
        intent, slots = await self.parse_scene_control(text)
        
        if intent == "unknown":
            return VoiceCommandResponse(
                success=False,
                intent=intent,
                slots=slots,
                message="抱歉，我无法识别您要触发的场景"
            )
        
        scene = slots["scene"]
        
        # 场景执行配置
        scene_configs = {
            "home": {
                "name": "回家模式",
                "actions": [
                    {"device": "客厅灯", "action": "turn_on"},
                    {"device": "空调", "action": "adjust", "params": {"temperature": 26}}
                ],
                "message": "欢迎回家！已为您打开客厅灯，空调已调至26度"
            },
            "leave": {
                "name": "离家模式",
                "actions": [
                    {"device": "所有灯", "action": "turn_off"},
                    {"device": "空调", "action": "turn_off"}
                ],
                "message": "离家模式已启动，已关闭所有电器"
            },
            "sleep": {
                "name": "睡眠模式",
                "actions": [
                    {"device": "卧室灯", "action": "turn_off"},
                    {"device": "窗帘", "action": "close"},
                    {"device": "空调", "action": "adjust", "params": {"temperature": 24}}
                ],
                "message": "晚安！已为您关闭灯光，拉上窗帘，空调调至24度"
            },
            "work": {
                "name": "工作模式",
                "actions": [
                    {"device": "书房灯", "action": "turn_on"},
                    {"device": "电脑", "action": "turn_on"}
                ],
                "message": "工作模式已启动，祝您工作顺利！"
            }
        }
        
        config = scene_configs.get(scene, {})
        
        # 记录用户行为
        await self._record_behavior(
            user_id=context.get("user_id", "default") if context else "default",
            action_type="scene_control",
            action_data={"scene": scene, "text": text}
        )
        
        # 构建执行动作
        action = {
            "type": "scene_control",
            "scene": scene,
            "scene_name": config.get("name", scene),
            "actions": config.get("actions", [])
        }
        
        # 生成建议
        suggestions = await self._generate_suggestions_after_action(
            action_type="scene_control",
            scene=scene,
            user_id=context.get("user_id", "default") if context else "default"
        )
        
        return VoiceCommandResponse(
            success=True,
            intent=intent,
            slots=slots,
            action=action,
            message=config.get("message", f"已执行{scene}场景"),
            suggestions=[s.dict() for s in suggestions]
        )
    
    # ═══════════════════════════════════════════════════════════════
    # 自然语言日程解析
    # ═══════════════════════════════════════════════════════════════
    
    async def parse_schedule(self, text: str, user_id: str = None) -> ScheduleParseResponse:
        """解析自然语言日程"""
        text = text.strip()
        
        # 提取事件标题
        title = await self._extract_event_title(text)
        
        # 提取时间
        start_time, end_time, recurrence = await self._extract_time_info(text)
        
        # 计算置信度
        confidence = self._calculate_parse_confidence(title, start_time)
        
        if confidence < 0.5:
            return ScheduleParseResponse(
                success=False,
                title=title,
                confidence=confidence
            )
        
        # 记录用户行为
        await self._record_behavior(
            user_id=user_id or "default",
            action_type="schedule_parse",
            action_data={"text": text, "title": title, "time": str(start_time)}
        )
        
        return ScheduleParseResponse(
            success=True,
            title=title,
            start_time=start_time,
            end_time=end_time,
            recurrence=recurrence,
            reminders=[start_time - timedelta(minutes=30)] if start_time else [],
            confidence=confidence
        )
    
    async def _extract_event_title(self, text: str) -> str:
        """提取事件标题"""
        # 移除时间相关词汇
        time_keywords = ["明天", "后天", "下周", "每天", "每周", "每月", "点", "分", "时", 
                         "上午", "下午", "晚上", "早上", "中午", "晚上"]
        
        title = text
        for keyword in time_keywords:
            title = re.sub(rf"{keyword}\S*", "", title)
        
        # 移除时间数字
        title = re.sub(r"\d+", "", title)
        
        # 移除常见动词
        verbs = ["提醒我", "安排", "设置", "创建", "添加", "有", "要"]
        for verb in verbs:
            title = title.replace(verb, "")
        
        return title.strip() or "新日程"
    
    async def _extract_time_info(self, text: str) -> Tuple[datetime, datetime, str]:
        """提取时间信息"""
        now = datetime.now()
        start_time = None
        end_time = None
        recurrence = None
        
        # 检查重复模式
        for pattern, rec_type in self.time_patterns["recurrence"]:
            match = re.search(pattern, text)
            if match:
                recurrence = rec_type
                break
        
        # 检查相对时间
        for pattern, delta in self.time_patterns["relative"]:
            match = re.search(pattern, text)
            if match:
                if isinstance(delta, timedelta):
                    start_time = (now + delta).replace(hour=9, minute=0, second=0, microsecond=0)
                elif isinstance(delta, str):
                    try:
                        amount = int(match.group(1))
                        if delta == "hours":
                            start_time = now + timedelta(hours=amount)
                        elif delta == "minutes":
                            start_time = now + timedelta(minutes=amount)
                        elif delta == "days":
                            start_time = (now + timedelta(days=amount)).replace(
                                hour=9, minute=0, second=0, microsecond=0
                            )
                    except (IndexError, ValueError):
                        pass
                break
        
        # 检查绝对时间
        if not start_time:
            for pattern, fmt in self.time_patterns["absolute"]:
                match = re.search(pattern, text)
                if match:
                    try:
                        time_str = match.group(0)
                        if "年" in time_str:
                            start_time = datetime.strptime(time_str, fmt)
                        elif "月" in time_str:
                            start_time = datetime.strptime(f"{now.year}年{time_str}", f"%Y年{fmt}")
                        else:
                            start_time = datetime.strptime(
                                f"{now.year}年{now.month}月{now.day}日{time_str}", 
                                f"%Y年%m月%d日{fmt}"
                            )
                        break
                    except ValueError:
                        continue
        
        # 默认时间处理
        if not start_time:
            # 检查是否有"明天"等关键词
            if "明天" in text:
                start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            elif "后天" in text:
                start_time = (now + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # 默认明天上午9点
                start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # 设置结束时间（默认1小时后）
        if start_time:
            end_time = start_time + timedelta(hours=1)
        
        return start_time, end_time, recurrence
    
    def _calculate_parse_confidence(self, title: str, start_time: datetime) -> float:
        """计算解析置信度"""
        confidence = 0.5
        
        if title and len(title) > 2:
            confidence += 0.2
        
        if start_time:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    # ═══════════════════════════════════════════════════════════════
    # 智能建议
    # ═══════════════════════════════════════════════════════════════
    
    async def get_suggestions(self, user_id: str = None, context: Dict[str, Any] = None) -> List[VoiceSuggestion]:
        """获取智能建议"""
        suggestions = []
        
        # 1. 基于时间的建议
        time_suggestions = await self._get_time_based_suggestions()
        suggestions.extend(time_suggestions)
        
        # 2. 基于习惯的建议
        habit_suggestions = await self._get_habit_based_suggestions(user_id or "default")
        suggestions.extend(habit_suggestions)
        
        # 3. 基于上下文的建议
        if context:
            context_suggestions = await self._get_context_based_suggestions(context)
            suggestions.extend(context_suggestions)
        
        # 4. 计算综合得分并排序
        scored_suggestions = []
        for suggestion in suggestions:
            score = await self._calculate_suggestion_score(suggestion, user_id)
            scored_suggestions.append((score, suggestion))
        
        scored_suggestions.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前5个建议
        return [s[1] for s in scored_suggestions[:5]]
    
    async def _get_time_based_suggestions(self) -> List[VoiceSuggestion]:
        """基于时间的建议"""
        now = datetime.now()
        hour = now.hour
        suggestions = []
        
        # 早上
        if 6 <= hour < 9:
            suggestions.append(VoiceSuggestion(
                type="scene",
                title="起床模式",
                description="打开窗帘、播放音乐、开启咖啡机",
                confidence=0.8,
                action={"type": "scene", "scene": "wake_up"},
                icon="morning"
            ))
        
        # 上午工作
        elif 9 <= hour < 12:
            suggestions.append(VoiceSuggestion(
                type="scene",
                title="工作模式",
                description="打开书房灯、启动电脑、设置专注模式",
                confidence=0.7,
                action={"type": "scene", "scene": "work"},
                icon="work"
            ))
        
        # 中午
        elif 11 <= hour < 14:
            suggestions.append(VoiceSuggestion(
                type="reminder",
                title="午餐提醒",
                description="该吃午饭了，是否需要点外卖？",
                confidence=0.6,
                action={"type": "reminder", "title": "午餐"},
                icon="food"
            ))
        
        # 晚上
        elif 18 <= hour < 22:
            suggestions.append(VoiceSuggestion(
                type="scene",
                title="回家模式",
                description="打开客厅灯、调节空调温度",
                confidence=0.9,
                action={"type": "scene", "scene": "home"},
                icon="home"
            ))
        
        # 深夜
        elif hour >= 22 or hour < 6:
            suggestions.append(VoiceSuggestion(
                type="scene",
                title="睡眠模式",
                description="关闭灯光、拉上窗帘、设置空调",
                confidence=0.8,
                action={"type": "scene", "scene": "sleep"},
                icon="night"
            ))
        
        return suggestions
    
    async def _get_habit_based_suggestions(self, user_id: str) -> List[VoiceSuggestion]:
        """基于习惯的建议"""
        suggestions = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询用户常用操作
            cursor.execute("""
                SELECT action_type, action_data, COUNT(*) as count
                FROM user_behaviors
                WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
                GROUP BY action_type, action_data
                ORDER BY count DESC
                LIMIT 5
            """, (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            for action_type, action_data, count in results:
                if count >= 3:  # 至少执行3次
                    try:
                        data = json.loads(action_data) if isinstance(action_data, str) else action_data
                        
                        if action_type == "device_control":
                            suggestions.append(VoiceSuggestion(
                                type="habit",
                                title=f"常用：{data.get('slots', {}).get('device', '设备')}",
                                description=f"您最近经常使用此操作",
                                confidence=min(0.5 + count * 0.05, 0.9),
                                action={"type": "device_control", "params": data.get("slots", {})},
                                icon="device"
                            ))
                    except (json.JSONDecodeError, AttributeError):
                        continue
        
        except Exception as e:
            logger.error(f"获取习惯建议失败: {e}")
        
        return suggestions
    
    async def _get_context_based_suggestions(self, context: Dict[str, Any]) -> List[VoiceSuggestion]:
        """基于上下文的建议"""
        suggestions = []
        
        # 位置上下文
        location = context.get("location")
        if location == "home":
            suggestions.append(VoiceSuggestion(
                type="scene",
                title="在家模式",
                description="根据您在家的场景推荐",
                confidence=0.7,
                action={"type": "scene", "scene": "home"},
                icon="home"
            ))
        
        # 活动上下文
        activity = context.get("activity")
        if activity == "watching_tv":
            suggestions.append(VoiceSuggestion(
                type="device",
                title="观影模式",
                description="调暗灯光、关闭窗帘",
                confidence=0.8,
                action={"type": "scene", "scene": "movie"},
                icon="movie"
            ))
        
        return suggestions
    
    async def _calculate_suggestion_score(self, suggestion: VoiceSuggestion, user_id: str) -> float:
        """计算建议得分"""
        score = suggestion.confidence
        
        # 基础分数
        base_score = score
        
        # 时间权重
        time_score = score * self.suggestion_weights["time"]
        
        # 习惯权重（从数据库查询）
        habit_score = score * self.suggestion_weights["habit"]
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_behaviors
                WHERE user_id = ? AND action_data LIKE ?
                AND timestamp >= datetime('now', '-7 days')
            """, (user_id, f"%{suggestion.title}%"))
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                habit_score *= (1 + count * 0.1)
        except:
            pass
        
        # 综合得分
        total_score = base_score * 0.5 + time_score + habit_score
        
        return min(total_score, 1.0)
    
    async def _generate_suggestions_after_action(
        self, action_type: str, device: str = None, scene: str = None, user_id: str = None
    ) -> List[VoiceSuggestion]:
        """执行动作后生成相关建议"""
        suggestions = []
        
        if action_type == "device_control" and device:
            # 设备控制后建议
            if "灯" in device:
                suggestions.append(VoiceSuggestion(
                    type="device",
                    title="调节亮度",
                    description=f"是否需要调节{device}的亮度？",
                    confidence=0.6,
                    action={"type": "device_control", "device": device, "action": "adjust_brightness"},
                    icon="light"
                ))
            elif "空调" in device:
                suggestions.append(VoiceSuggestion(
                    type="device",
                    title="设置温度",
                    description="建议设置到舒适的温度（26度）",
                    confidence=0.7,
                    action={"type": "device_control", "device": device, "action": "set_temperature", "value": 26},
                    icon="temperature"
                ))
        
        elif action_type == "scene_control" and scene:
            # 场景控制后建议
            if scene == "home":
                suggestions.append(VoiceSuggestion(
                    type="reminder",
                    title="查看日程",
                    description="查看今天的日程安排",
                    confidence=0.6,
                    action={"type": "query", "target": "calendar"},
                    icon="calendar"
                ))
            elif scene == "sleep":
                suggestions.append(VoiceSuggestion(
                    type="reminder",
                    title="设置闹钟",
                    description="是否需要设置明天的闹钟？",
                    confidence=0.8,
                    action={"type": "reminder", "action": "set_alarm"},
                    icon="alarm"
                ))
        
        return suggestions
    
    # ═══════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════
    
    async def _record_behavior(self, user_id: str, action_type: str, action_data: Dict[str, Any]):
        """记录用户行为"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_behaviors (user_id, action_type, action_data, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (user_id, action_type, json.dumps(action_data, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录用户行为失败: {e}")
    
    async def _update_device_stats(self, device_id: str, action: str):
        """更新设备使用统计"""
        try:
            now = datetime.now()
            time_slot = f"{now.hour:02d}:00"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO device_usage_stats (device_id, action, count, last_used, time_slot)
                VALUES (?, ?, 1, datetime('now'), ?)
                ON CONFLICT(device_id, action, time_slot)
                DO UPDATE SET count = count + 1, last_used = datetime('now')
            """, (device_id, action, time_slot))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新设备统计失败: {e}")
    
    async def process_voice_command(self, request: VoiceCommandRequest) -> VoiceCommandResponse:
        """处理语音命令（统一入口）"""
        text = request.text.strip()
        
        # 1. 尝试解析为设备控制
        intent, slots = await self.parse_device_control(text)
        if intent != "unknown":
            return await self.execute_device_control(text, request.context or {})
        
        # 2. 尝试解析为场景控制
        intent, slots = await self.parse_scene_control(text)
        if intent != "unknown":
            return await self.execute_scene_control(text, request.context or {})
        
        # 3. 无法识别
        return VoiceCommandResponse(
            success=False,
            intent="unknown",
            slots={},
            message="抱歉，我无法理解您的命令。您可以尝试说：'打开客厅的灯' 或 '我要睡觉了'"
        )


# ═══════════════════════════════════════════════════════════════
# 服务实例
# ═══════════════════════════════════════════════════════════════

voice_enhanced_service = VoiceEnhancedService()