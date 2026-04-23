#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家庭财务服务
记账、预算、报表、资产管理
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def _get_db():
    """获取数据库连接"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn

def _init_db(conn):
    """初始化数据库"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            UNIQUE(category, month)
        )
    ''')
    conn.commit()

async def add_transaction(
    amount: float,
    category: str,
    type: str,
    description: str = "",
    date: Optional[str] = None
) -> Dict[str, Any]:
    """添加交易记录"""
    if not date:
        date = datetime.now().isoformat()
    
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (amount, category, type, description, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (amount, category, type, description, date))
    conn.commit()
    
    transaction_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"Transaction added: {transaction_id}, {type}, {amount}, {category}")
    
    return {
        "id": transaction_id,
        "amount": amount,
        "category": category,
        "type": type,
        "description": description,
        "date": date
    }

async def query_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """查询交易"""
    conn = _get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    transactions = [dict(row) for row in rows]
    
    return {"transactions": transactions, "total": len(transactions)}

async def get_daily_report(date: Optional[str] = None) -> Dict[str, Any]:
    """日报"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = _get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, category, SUM(amount) as total, COUNT(*) as count
        FROM transactions
        WHERE date LIKE ?
        GROUP BY type, category
    ''', (f"{date}%",))
    
    rows = cursor.fetchall()
    conn.close()
    
    income = sum(row["total"] for row in rows if row["type"] == "income")
    expense = sum(row["total"] for row in rows if row["type"] == "expense")
    
    return {
        "date": date,
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "categories": [dict(row) for row in rows]
    }

async def get_monthly_report(month: Optional[str] = None) -> Dict[str, Any]:
    """月报"""
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    conn = _get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, category, SUM(amount) as total
        FROM transactions
        WHERE date LIKE ?
        GROUP BY type, category
    ''', (f"{month}%",))
    
    rows = cursor.fetchall()
    conn.close()
    
    income = sum(row["total"] for row in rows if row["type"] == "income")
    expense = sum(row["total"] for row in rows if row["type"] == "expense")
    
    # 按类别统计
    categories = {}
    for row in rows:
        if row["type"] == "expense":
            categories[row["category"]] = row["total"]
    
    return {
        "month": month,
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "categories": categories
    }

async def get_budget_status() -> Dict[str, Any]:
    """预算状态"""
    month = datetime.now().strftime("%Y-%m")
    
    conn = _get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM budgets WHERE month = ?', (month,))
    budgets = cursor.fetchall()
    
    # 获取实际支出
    cursor.execute('''
        SELECT category, SUM(amount) as spent
        FROM transactions
        WHERE type = 'expense' AND date LIKE ?
        GROUP BY category
    ''', (f"{month}%",))
    spent = {row["category"]: row["spent"] for row in cursor.fetchall()}
    
    conn.close()
    
    budget_status = []
    for budget in budgets:
        budget_dict = dict(budget)
        budget_dict["spent"] = spent.get(budget["category"], 0)
        budget_dict["remaining"] = budget["amount"] - budget_dict["spent"]
        budget_dict["percentage"] = (budget_dict["spent"] / budget["amount"] * 100) if budget["amount"] > 0 else 0
        budget_status.append(budget_dict)
    
    return {"budgets": budget_status, "month": month}

async def get_asset_summary() -> Dict[str, Any]:
    """资产汇总"""
    # TODO: 实现资产管理
    return {
        "total": 0,
        "accounts": {
            "cash": 0,
            "bank": 0,
            "alipay": 0,
            "wechat": 0,
            "credit_card": 0
        }
    }
