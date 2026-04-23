#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日程管理服务 - SQLite持久化版本"""
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CalendarService:
    """日程管理服务"""
    
    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        self._conn = None
        self._init_db()
    
    def _get_conn(self):
        """获取数据库连接（复用连接）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        """初始化数据库表"""
        c = self._get_conn().cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                description TEXT,
                location TEXT,
                reminder_minutes INTEGER DEFAULT 30,
                repeat_type TEXT DEFAULT 'none',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP
            )
        ''')
        self._conn.commit()
        logger.info("Calendar service database initialized")
    
    async def create_event(self, title: str, start_time: str, end_time: str = None,
                          description: str = None, location: str = None,
                          reminder_minutes: int = 30, repeat_type: str = 'none') -> Dict[str, Any]:
        """
        创建日程事件
        
        Args:
            title: 事件标题
            start_time: 开始时间 (格式: YYYY-MM-DD HH:MM 或 YYYY-MM-DD)
            end_time: 结束时间（可选）
            description: 描述
            location: 地点
            reminder_minutes: 提醒时间（分钟）
            repeat_type: 重复类型 (none/daily/weekly/monthly/yearly)
        
        Returns:
            创建的事件信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            event_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            now = datetime.now()
            
            c.execute('''
                INSERT INTO calendar_events 
                (event_id, title, start_time, end_time, description, location, 
                 reminder_minutes, repeat_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            ''', (event_id, title, start_time, end_time, description, location,
                  reminder_minutes, repeat_type, now))
            
            conn.commit()
            
            logger.info(f"Calendar event created: {title} (ID: {event_id})")
            
            return {
                "id": event_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "location": location,
                "reminder_minutes": reminder_minutes,
                "repeat_type": repeat_type,
                "status": "active",
                "created_at": now.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return {"error": str(e)}
    
    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        获取单个事件
        
        Args:
            event_id: 事件ID
        
        Returns:
            事件信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM calendar_events WHERE event_id = ?', (event_id,))
        row = c.fetchone()
        
        if row:
            return self._row_to_event(row)
        
        return {"error": "Event not found"}
    
    async def list_events(self, start_date: str = None, end_date: str = None,
                         status: str = None) -> Dict[str, Any]:
        """
        获取日程列表
        
        Args:
            start_date: 开始日期筛选 (YYYY-MM-DD)
            end_date: 结束日期筛选 (YYYY-MM-DD)
            status: 状态筛选 (active/completed/cancelled)
        
        Returns:
            事件列表
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        query = "SELECT * FROM calendar_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date(start_time) >= date(?)"
            params.append(start_date)
        
        if end_date:
            query += " AND date(start_time) <= date(?)"
            params.append(end_date)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY start_time ASC"
        
        c.execute(query, params)
        
        events = []
        for row in c.fetchall():
            events.append(self._row_to_event(row))
        
        return {"events": events, "count": len(events)}
    
    async def get_today(self) -> Dict[str, Any]:
        """
        获取今日日程
        
        Returns:
            今日事件列表
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM calendar_events 
            WHERE date(start_time) = date(?) AND status = 'active'
            ORDER BY start_time ASC
        ''', (today,))
        
        events = []
        for row in c.fetchall():
            events.append(self._row_to_event(row))
        
        return {
            "events": events,
            "date": today,
            "count": len(events)
        }
    
    async def get_upcoming(self, days: int = 7) -> Dict[str, Any]:
        """
        获取即将到来的日程
        
        Args:
            days: 未来天数
        
        Returns:
            即将到来的事件列表
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM calendar_events 
            WHERE date(start_time) >= date('now') 
            AND date(start_time) <= date('now', ?)
            AND status = 'active'
            ORDER BY start_time ASC
        ''', (f'+{days} days',))
        
        events = []
        for row in c.fetchall():
            events.append(self._row_to_event(row))
        
        return {
            "events": events,
            "count": len(events),
            "days": days
        }
    
    async def update_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新事件
        
        Args:
            event_id: 事件ID
            **kwargs: 要更新的字段 (title, start_time, end_time, description, 
                      location, reminder_minutes, repeat_type, status)
        
        Returns:
            更新后的事件信息
        """
        allowed_fields = ['title', 'start_time', 'end_time', 'description',
                         'location', 'reminder_minutes', 'repeat_type', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return {"error": "No valid fields to update"}
        
        conn = self._get_conn()
        c = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [event_id]
        
        c.execute(f"UPDATE calendar_events SET {set_clause} WHERE event_id = ?", values)
        
        if c.rowcount == 0:
            return {"error": "Event not found"}
        
        conn.commit()
        
        c.execute('SELECT * FROM calendar_events WHERE event_id = ?', (event_id,))
        row = c.fetchone()
        
        logger.info(f"Calendar event updated: {event_id}")
        
        return self._row_to_event(row)
    
    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        删除事件
        
        Args:
            event_id: 事件ID
        
        Returns:
            操作结果
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM calendar_events WHERE event_id = ?', (event_id,))
        
        if c.rowcount == 0:
            return {"error": "Event not found"}
        
        conn.commit()
        
        logger.info(f"Calendar event deleted: {event_id}")
        return {"success": True, "message": f"Event {event_id} deleted"}
    
    async def get_countdown(self, event_name: str = None, event_id: str = None) -> Dict[str, Any]:
        """
        计算倒计时
        
        Args:
            event_name: 事件名称（模糊匹配）
            event_id: 事件ID（精确匹配）
        
        Returns:
            倒计时信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        if event_id:
            c.execute('''
                SELECT * FROM calendar_events 
                WHERE event_id = ? AND status = 'active'
            ''', (event_id,))
        elif event_name:
            c.execute('''
                SELECT * FROM calendar_events 
                WHERE title LIKE ? AND status = 'active'
                ORDER BY start_time ASC
                LIMIT 1
            ''', (f'%{event_name}%',))
        else:
            return {"error": "Please provide event_name or event_id"}
        
        row = c.fetchone()
        
        if not row:
            return {"error": "Event not found"}
        
        event = self._row_to_event(row)
        
        try:
            event_date = datetime.strptime(event['start_time'][:10], "%Y-%m-%d")
            now = datetime.now()
            today = datetime(now.year, now.month, now.day)
            
            days_remaining = (event_date - today).days
            
            if days_remaining < 0:
                status_text = "已过期"
                days_text = f"已过去 {abs(days_remaining)} 天"
            elif days_remaining == 0:
                status_text = "今天"
                days_text = "就是今天"
            else:
                status_text = f"还有 {days_remaining} 天"
                days_text = f"还有 {days_remaining} 天"
            
            return {
                "event": event,
                "days_remaining": days_remaining,
                "status": status_text,
                "message": f"「{event['title']}」{days_text}",
                "target_date": event['start_time'][:10]
            }
        except Exception as e:
            return {"error": f"Date parsing error: {e}"}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM calendar_events')
        total = c.fetchone()['total']
        
        c.execute("SELECT COUNT(*) as count FROM calendar_events WHERE status = 'active'")
        active = c.fetchone()['count']
        
        c.execute("SELECT COUNT(*) as count FROM calendar_events WHERE status = 'completed'")
        completed = c.fetchone()['count']
        
        c.execute('''
            SELECT COUNT(*) as count FROM calendar_events 
            WHERE date(start_time) >= date('now') AND status = 'active'
        ''')
        upcoming = c.fetchone()['count']
        
        c.execute('''
            SELECT COUNT(*) as count FROM calendar_events 
            WHERE date(start_time) = date('now') AND status = 'active'
        ''')
        today = c.fetchone()['count']
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "upcoming": upcoming,
            "today": today
        }
    
    def _row_to_event(self, row) -> Dict[str, Any]:
        """将数据库行转换为事件字典"""
        return {
            "id": row['event_id'],
            "title": row['title'],
            "start_time": row['start_time'],
            "end_time": row['end_time'],
            "description": row['description'],
            "location": row['location'],
            "reminder_minutes": row['reminder_minutes'],
            "repeat_type": row['repeat_type'],
            "status": row['status'],
            "created_at": row['created_at']
        }
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[CalendarService] = None


def get_service() -> CalendarService:
    """获取日程服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = CalendarService()
    return _service_instance


async def create_event(title: str, start_time: str, end_time: str = None, 
                       description: str = None, **kwargs) -> Dict[str, Any]:
    """创建事件（兼容旧接口）"""
    return await get_service().create_event(title, start_time, end_time, description, **kwargs)


async def list_events(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """获取日程列表（兼容旧接口）"""
    return await get_service().list_events(start_date, end_date)


async def get_today() -> Dict[str, Any]:
    """获取今日日程（兼容旧接口）"""
    return await get_service().get_today()


async def get_countdown(event_name: str = None) -> Dict[str, Any]:
    """计算倒计时（兼容旧接口）"""
    return await get_service().get_countdown(event_name=event_name)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = CalendarService(':memory:')
        
        print("=== 日程管理服务测试 ===\n")
        
        print("1. 创建日程事件...")
        event1 = await service.create_event(
            title="团队周会",
            start_time="2025-03-20 10:00",
            end_time="2025-03-20 11:00",
            description="每周团队例会",
            location="会议室A"
        )
        print(f"   创建: {event1['id']} - {event1['title']}")
        
        event2 = await service.create_event(
            title="项目评审",
            start_time="2025-03-18 14:00",
            description="Q1项目评审会议",
            location="会议室B",
            reminder_minutes=60
        )
        print(f"   创建: {event2['id']} - {event2['title']}")
        
        event3 = await service.create_event(
            title="生日聚会",
            start_time="2025-03-25 18:00",
            description="庆祝生日",
            location="餐厅",
            repeat_type="yearly"
        )
        print(f"   创建: {event3['id']} - {event3['title']}")
        
        today_event = await service.create_event(
            title="今日待办",
            start_time=datetime.now().strftime("%Y-%m-%d 15:00"),
            description="今天要完成的任务"
        )
        print(f"   创建: {today_event['id']} - {today_event['title']}")
        
        print("\n2. 获取日程列表...")
        events = await service.list_events()
        print(f"   共 {events['count']} 个事件")
        for e in events['events']:
            print(f"   - [{e['status']}] {e['title']} @ {e['start_time']}")
        
        print("\n3. 获取今日日程...")
        today = await service.get_today()
        print(f"   今日({today['date']})共 {today['count']} 个事件")
        for e in today['events']:
            print(f"   - {e['title']} @ {e['start_time']}")
        
        print("\n4. 获取即将到来的日程...")
        upcoming = await service.get_upcoming(days=7)
        print(f"   未来7天共 {upcoming['count']} 个事件")
        for e in upcoming['events']:
            print(f"   - {e['title']} @ {e['start_time']}")
        
        print("\n5. 计算倒计时...")
        countdown = await service.get_countdown(event_name="生日")
        print(f"   {countdown.get('message', countdown)}")
        
        countdown2 = await service.get_countdown(event_id=event2['id'])
        print(f"   {countdown2.get('message', countdown2)}")
        
        print("\n6. 更新事件...")
        updated = await service.update_event(event1['id'], status='completed', description='会议已完成')
        print(f"   更新结果: {updated.get('status', updated)}")
        
        print("\n7. 获取统计信息...")
        stats = await service.get_statistics()
        print(f"   {stats}")
        
        print("\n8. 删除事件...")
        result = await service.delete_event(event3['id'])
        print(f"   {result}")
        
        print("\n9. 再次获取列表验证删除...")
        events = await service.list_events()
        print(f"   剩余 {events['count']} 个事件")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())