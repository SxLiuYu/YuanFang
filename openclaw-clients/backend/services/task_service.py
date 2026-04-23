#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理服务
任务创建、分配、完成、积分系统
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn

def _init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assignee TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'normal',
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            UNIQUE(user_id)
        )
    ''')
    conn.commit()

async def create_task(
    title: str,
    description: str = "",
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """创建任务"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, assignee, due_date, priority)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, assignee, due_date, priority))
    conn.commit()
    
    task_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"Task created: {task_id}, title={title}, assignee={assignee}")
    
    return {
        "id": task_id,
        "title": title,
        "description": description,
        "assignee": assignee,
        "status": "pending",
        "priority": priority,
        "due_date": due_date
    }

async def list_tasks(status: Optional[str] = None, assignee: Optional[str] = None) -> Dict[str, Any]:
    """任务列表"""
    conn = _get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if assignee:
        query += " AND assignee = ?"
        params.append(assignee)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tasks = [dict(row) for row in rows]
    return {"tasks": tasks, "total": len(tasks)}

async def complete_task(task_id: str) -> Dict[str, Any]:
    """完成任务"""
    conn = _get_db()
    cursor = conn.cursor()
    
    completed_at = datetime.now().isoformat()
    cursor.execute('''
        UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?
    ''', (completed_at, task_id))
    conn.commit()
    
    # 获取任务信息
    cursor.execute('SELECT assignee FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    
    # 添加积分
    if row and row["assignee"]:
        cursor.execute('''
            INSERT INTO points (user_id, points) VALUES (?, 10)
            ON CONFLICT(user_id) DO UPDATE SET points = points + 10
        ''', (row["assignee"],))
        conn.commit()
    
    conn.close()
    
    logger.info(f"Task completed: {task_id}")
    
    return {"id": task_id, "status": "completed", "completed_at": completed_at}

async def get_completion_stats() -> Dict[str, Any]:
    """任务完成率"""
    conn = _get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    conn.close()
    
    rate = (completed / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "completion_rate": round(rate, 2)
    }

async def get_ranking() -> Dict[str, Any]:
    """任务排行榜"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    ranking = [{"user_id": row["user_id"], "points": row["points"]} for row in rows]
    return {"ranking": ranking}
