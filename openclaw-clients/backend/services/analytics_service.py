#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw - 高级分析服务
支持健康评分、消费洞察、异常预警、报告生成

Author: 于金泽
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

class HealthScoreRequest(BaseModel):
    user_id: str
    device_id: Optional[str] = None

class FinanceInsightRequest(BaseModel):
    user_id: str
    period_days: int = 30

class AnomalyCheckRequest(BaseModel):
    user_id: str
    data_type: str  # "health", "finance"
    threshold: Optional[float] = None

class ReportGenerateRequest(BaseModel):
    user_id: str
    report_type: str  # "weekly", "monthly"
    include_sections: List[str] = ["health", "finance", "tasks"]

# ═══════════════════════════════════════════════════════════════
# 分析服务类
# ═══════════════════════════════════════════════════════════════

class AnalyticsService:
    """高级分析服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent.parent / "data" / "analytics.db")
        self._init_database()
    
    def _init_database(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                data TEXT,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                severity TEXT DEFAULT 'warning',
                message TEXT,
                details TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_resolved INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 健康评分
    # ═══════════════════════════════════════════════════════════════
    
    async def calculate_health_score(self, request: HealthScoreRequest) -> Dict[str, Any]:
        """计算健康评分（0-100）"""
        hardware_db = Path(self.db_path).parent / "hardware.db"
        
        if not hardware_db.exists():
            return {"success": False, "message": "无健康数据", "score": 0}
        
        conn = sqlite3.connect(str(hardware_db))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    AVG(heart_rate) as avg_hr,
                    SUM(steps) as total_steps,
                    AVG(sleep_duration) as avg_sleep,
                    SUM(calories) as total_calories,
                    AVG(blood_oxygen) as avg_oxygen
                FROM watch_data
                WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
            """, (request.user_id,))
            
            row = cursor.fetchone()
            
            if not row or row[0] is None:
                return {"success": False, "message": "数据不足", "score": 0}
            
            avg_hr, total_steps, avg_sleep, total_calories, avg_oxygen = row
            
            # 计算各维度得分
            heart_score = self._calculate_heart_score(avg_hr)
            steps_score = self._calculate_steps_score(total_steps / 7 if total_steps else 0)
            sleep_score = self._calculate_sleep_score(avg_sleep)
            oxygen_score = self._calculate_oxygen_score(avg_oxygen)
            
            # 加权平均
            total_score = (
                heart_score * 0.3 +
                steps_score * 0.3 +
                sleep_score * 0.25 +
                oxygen_score * 0.15
            )
            
            return {
                "success": True,
                "score": round(total_score, 1),
                "components": {
                    "heart_rate": {"score": heart_score, "value": round(avg_hr, 1) if avg_hr else None},
                    "steps": {"score": steps_score, "value": int(total_steps) if total_steps else 0},
                    "sleep": {"score": sleep_score, "value": round(avg_sleep, 1) if avg_sleep else None},
                    "oxygen": {"score": oxygen_score, "value": round(avg_oxygen, 1) if avg_oxygen else None}
                },
                "grade": self._get_grade(total_score),
                "suggestions": self._get_health_suggestions(total_score, heart_score, steps_score, sleep_score)
            }
        finally:
            conn.close()
    
    def _calculate_heart_score(self, avg_hr: float) -> float:
        if avg_hr is None: return 50
        if 60 <= avg_hr <= 100: return 100
        if 50 <= avg_hr < 60 or 100 < avg_hr <= 110: return 80
        return 60
    
    def _calculate_steps_score(self, avg_daily_steps: float) -> float:
        if avg_daily_steps >= 10000: return 100
        if avg_daily_steps >= 8000: return 90
        if avg_daily_steps >= 5000: return 70
        return 50
    
    def _calculate_sleep_score(self, avg_sleep: float) -> float:
        if avg_sleep is None: return 50
        if 7 <= avg_sleep <= 9: return 100
        if 6 <= avg_sleep < 7 or 9 < avg_sleep <= 10: return 80
        return 60
    
    def _calculate_oxygen_score(self, avg_oxygen: float) -> float:
        if avg_oxygen is None: return 50
        if avg_oxygen >= 95: return 100
        if avg_oxygen >= 90: return 80
        return 60
    
    def _get_grade(self, score: float) -> str:
        if score >= 90: return "优秀"
        if score >= 80: return "良好"
        if score >= 70: return "一般"
        if score >= 60: return "需改善"
        return "需关注"
    
    def _get_health_suggestions(self, total: float, heart: float, steps: float, sleep: float) -> List[str]:
        suggestions = []
        if steps < 70: suggestions.append("建议每天步行达到8000步以上")
        if sleep < 70: suggestions.append("建议保持每天7-8小时睡眠")
        if heart < 70: suggestions.append("建议关注心率变化，必要时咨询医生")
        if total >= 80: suggestions.append("继续保持良好的生活习惯！")
        return suggestions
    
    # ═══════════════════════════════════════════════════════════════
    # 消费洞察
    # ═══════════════════════════════════════════════════════════════
    
    async def get_finance_insights(self, request: FinanceInsightRequest) -> Dict[str, Any]:
        """获取消费洞察"""
        finance_db = Path(self.db_path).parent / "finance.db"
        
        if not finance_db.exists():
            return {"success": False, "message": "无财务数据"}
        
        conn = sqlite3.connect(str(finance_db))
        cursor = conn.cursor()
        
        try:
            # 消费分类统计
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type = 'expense' AND date >= datetime('now', ?)
                GROUP BY category ORDER BY total DESC
            """, (f'-{request.period_days} days',))
            
            categories = [{"category": row[0], "amount": row[1]} for row in cursor.fetchall()]
            
            # 总消费
            cursor.execute("""
                SELECT SUM(amount) FROM transactions
                WHERE type = 'expense' AND date >= datetime('now', ?)
            """, (f'-{request.period_days} days',))
            total_expense = cursor.fetchone()[0] or 0
            
            # 总收入
            cursor.execute("""
                SELECT SUM(amount) FROM transactions
                WHERE type = 'income' AND date >= datetime('now', ?)
            """, (f'-{request.period_days} days',))
            total_income = cursor.fetchone()[0] or 0
            
            # 生成洞察
            insights = []
            if categories:
                top_category = categories[0]
                insights.append(f"最大支出类别: {top_category['category']}（{top_category['amount']}元）")
            
            if total_income > 0:
                savings_rate = (total_income - total_expense) / total_income * 100
                insights.append(f"储蓄率: {savings_rate:.1f}%")
            
            return {
                "success": True,
                "period_days": request.period_days,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
                "categories": categories[:5],
                "insights": insights
            }
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 异常预警
    # ═══════════════════════════════════════════════════════════════
    
    async def check_anomalies(self, request: AnomalyCheckRequest) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        if request.data_type == "health":
            health_anomalies = await self._check_health_anomalies(request.user_id)
            anomalies.extend(health_anomalies)
        elif request.data_type == "finance":
            finance_anomalies = await self._check_finance_anomalies(request.user_id)
            anomalies.extend(finance_anomalies)
        
        # 记录异常
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for anomaly in anomalies:
            cursor.execute("""
                INSERT INTO anomaly_records (user_id, type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            """, (request.user_id, anomaly["type"], anomaly["severity"],
                  anomaly["message"], json.dumps(anomaly.get("details", {}))))
        conn.commit()
        conn.close()
        
        return anomalies
    
    async def _check_health_anomalies(self, user_id: str) -> List[Dict[str, Any]]:
        anomalies = []
        hardware_db = Path(self.db_path).parent / "hardware.db"
        
        if not hardware_db.exists():
            return anomalies
        
        conn = sqlite3.connect(str(hardware_db))
        cursor = conn.cursor()
        
        try:
            # 检查心率异常
            cursor.execute("""
                SELECT AVG(heart_rate), MAX(heart_rate), MIN(heart_rate)
                FROM watch_data WHERE user_id = ? AND timestamp >= datetime('now', '-1 day')
            """, (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                avg_hr, max_hr, min_hr = row
                if max_hr and max_hr > 120:
                    anomalies.append({
                        "type": "heart_rate_high",
                        "severity": "warning",
                        "message": f"检测到心率异常偏高: 最高{max_hr}次/分",
                        "details": {"avg": avg_hr, "max": max_hr, "min": min_hr}
                    })
            
            # 检查血氧
            cursor.execute("""
                SELECT AVG(blood_oxygen), MIN(blood_oxygen)
                FROM watch_data WHERE user_id = ? AND timestamp >= datetime('now', '-1 day')
            """, (user_id,))
            row = cursor.fetchone()
            if row and row[1] and row[1] < 90:
                anomalies.append({
                    "type": "blood_oxygen_low",
                    "severity": "critical",
                    "message": f"检测到血氧过低: 最低{row[1]}%",
                    "details": {"min": row[1], "avg": row[0]}
                })
        finally:
            conn.close()
        
        return anomalies
    
    async def _check_finance_anomalies(self, user_id: str) -> List[Dict[str, Any]]:
        anomalies = []
        finance_db = Path(self.db_path).parent / "finance.db"
        
        if not finance_db.exists():
            return anomalies
        
        conn = sqlite3.connect(str(finance_db))
        cursor = conn.cursor()
        
        try:
            # 检查大额支出
            cursor.execute("""
                SELECT amount, category, description
                FROM transactions WHERE type = 'expense'
                AND date >= datetime('now', '-7 days')
                ORDER BY amount DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row and row[0] > 1000:
                anomalies.append({
                    "type": "large_expense",
                    "severity": "info",
                    "message": f"本周大额支出: {row[0]}元（{row[1]}）",
                    "details": {"amount": row[0], "category": row[1]}
                })
        finally:
            conn.close()
        
        return anomalies
    
    # ═══════════════════════════════════════════════════════════════
    # 报告生成
    # ═══════════════════════════════════════════════════════════════
    
    async def generate_report(self, request: ReportGenerateRequest) -> Dict[str, Any]:
        """生成报告"""
        now = datetime.now()
        
        if request.report_type == "weekly":
            start_date = now - timedelta(days=7)
            period_name = f"{start_date.strftime('%m月%d日')}-{now.strftime('%m月%d日')}"
        else:
            start_date = now - timedelta(days=30)
            period_name = f"{start_date.strftime('%m月%d日')}-{now.strftime('%m月%d日')}"
        
        report = {
            "success": True,
            "report_type": request.report_type,
            "period": period_name,
            "generated_at": now.isoformat(),
            "sections": {}
        }
        
        if "health" in request.include_sections:
            health_score = await self.calculate_health_score(
                HealthScoreRequest(user_id=request.user_id)
            )
            report["sections"]["health"] = health_score
        
        if "finance" in request.include_sections:
            finance_insights = await self.get_finance_insights(
                FinanceInsightRequest(user_id=request.user_id)
            )
            report["sections"]["finance"] = finance_insights
        
        return report


analytics_service = AnalyticsService()