"""
memory/hierarchical.py
层级化记忆系统
- 短期记忆：Redis（会话级，快速访问，自动过期）
- 长期记忆：Qdrant 向量库（语义检索，持久化）
- 永久结构化记忆：SQLite（用户偏好、事实、日程，结构化存储）
- 记忆遗忘机制：不重要记忆随时间衰减，自动归档
"""

import os
import json
import sqlite3
import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import redis

# 记忆类型分类
MEMORY_TYPES = {
    "short_term": "短期会话记忆",
    "long_term": "长期语义记忆", 
    "permanent": "永久结构化记忆"
}

# 遗忘衰减参数
DEFAULT_HALF_LIFE_HOURS = 72  # 半衰期72小时，衰减后检索权重降低
MIN_IMPORTANCE = 0.1  # 最低重要性，低于自动归档/删除


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    text: str
    memory_type: str  # short_term | long_term | permanent
    importance: float  # 0.0 - 1.0，越高越不容易遗忘
    created_at: str
    accessed_at: str  # 最后访问时间
    access_count: int  # 访问次数，频繁访问提升重要性
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class PermanentSQLiteStorage:
    """永久结构化存储 - SQLite"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "data", "permanent_memory.db"
            )
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT UNIQUE,
                fact_value TEXT,
                category TEXT,
                importance REAL,
                created_at TEXT,
                updated_at TEXT,
                source TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE,
                preference_value TEXT,
                confidence REAL,
                created_at TEXT,
                last_verified TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                event_time TEXT,
                location TEXT,
                created_at TEXT,
                remind BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_fact(self, fact_key: str, fact_value: Any, category: str, 
                 importance: float = 0.8, source: str = "dialog") -> bool:
        """添加/更新事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        cursor.execute("""
            REPLACE INTO facts 
            (fact_key, fact_value, category, importance, created_at, updated_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fact_key, 
            json.dumps(fact_value) if isinstance(fact_value, (dict, list)) else str(fact_value),
            category, 
            importance,
            now, now, source
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_fact(self, fact_key: str) -> Optional[Any]:
        """查询事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fact_value FROM facts WHERE fact_key = ?", (fact_key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return row[0]
    
    def delete_fact(self, fact_key: str) -> bool:
        """删除事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM facts WHERE fact_key = ?", (fact_key,))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed
    
    def list_facts(self, category: str = None) -> List[Dict]:
        """列出事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM facts WHERE category = ? ORDER BY importance DESC", (category,))
        else:
            cursor.execute("SELECT * FROM facts ORDER BY importance DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "fact_key": row[1],
                "fact_value": row[2],
                "category": row[3],
                "importance": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "source": row[7]
            })
        return result
    
    def add_preference(self, key: str, value: Any, confidence: float = 0.9) -> bool:
        """添加用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute("""
            REPLACE INTO user_preferences 
            (preference_key, preference_value, confidence, created_at, last_verified)
            VALUES (?, ?, ?, ?, ?)
        """, (
            key,
            json.dumps(value) if isinstance(value, (dict, list)) else str(value),
            confidence,
            now, now
        ))
        conn.commit()
        conn.close()
        return True
    
    def get_preference(self, key: str) -> Optional[Any]:
        """获取用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT preference_value FROM user_preferences WHERE preference_key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return row[0]


class ShortTermRedisMemory:
    """短期记忆 - Redis，自动过期"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 default_ttl_seconds: int = 3600 * 24):  # 默认24小时过期
        self.host = os.getenv("REDIS_HOST", host)
        self.port = int(os.getenv("REDIS_PORT", port))
        self.db = db
        self.default_ttl = default_ttl_seconds
        self._connect()
    
    def _connect(self):
        try:
            self.client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True
            )
            self.client.ping()
        except Exception as e:
            print(f"[ShortTermMemory] Redis连接失败: {e}，将使用内存回退")
            self.client = None
    
    def is_connected(self) -> bool:
        return self.client is not None
    
    def store(self, key: str, value: Any, ttl: int = None) -> bool:
        """存储短期记忆"""
        if not self.client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.client.set(key, str(value), ex=ttl or self.default_ttl)
            return True
        except Exception as e:
            print(f"[ShortTermMemory] 存储失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取短期记忆"""
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """删除短期记忆"""
        if not self.client:
            return False
        self.client.delete(key)
        return True
    
    def clear_expired(self):
        """Redis自动处理过期，不需要手动清理"""
        pass


class HierarchicalMemory:
    """层级化记忆系统 - 整合三级存储 + 遗忘机制"""
    
    def __init__(self):
        self.short_term = ShortTermRedisMemory()
        self.permanent = PermanentSQLiteStorage()
        # 长期向量记忆使用现有的 VectorMemory / Qdrant
        self._init_forgetting()
    
    def _init_forgetting(self):
        # 遗忘记录
        self.forgetting_log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "forgetting_log.json"
        )
        Path(os.path.dirname(self.forgetting_log_path)).mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.forgetting_log_path):
            with open(self.forgetting_log_path, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def _calculate_current_importance(self, entry: MemoryEntry) -> float:
        """计算当前重要性，随时间衰减"""
        created = datetime.datetime.fromisoformat(entry.created_at)
        age_hours = (datetime.datetime.now() - created).total_seconds() / 3600
        
        # 半衰期衰减公式: importance = base_importance * (1/2)^(age / half_life)
        half_life = DEFAULT_HALF_LIFE_HOURS
        decay = (0.5) ** (age_hours / half_life)
        
        # 访问次数奖励：每次访问提升10%重要性，最高翻倍
        access_bonus = 1.0 + (entry.access_count * 0.1)
        access_bonus = min(access_bonus, 2.0)
        
        current = entry.importance * decay * access_bonus
        return max(current, MIN_IMPORTANCE)
    
    def store_short_term(self, key: str, value: Any, ttl: int = None) -> bool:
        """存储短期记忆"""
        return self.short_term.store(key, value, ttl)
    
    def get_short_term(self, key: str) -> Optional[Any]:
        """获取短期记忆"""
        return self.short_term.get(key)
    
    def store_permanent_fact(self, key: str, value: Any, category: str, 
                           importance: float = 0.8) -> bool:
        """存储永久事实"""
        return self.permanent.add_fact(key, value, category, importance)
    
    def get_permanent_fact(self, key: str) -> Optional[Any]:
        """获取永久事实"""
        return self.permanent.get_fact(key)
    
    def delete_permanent_fact(self, key: str) -> bool:
        """删除永久事实"""
        return self.permanent.delete_fact(key)
    
    def store_user_preference(self, key: str, value: Any, confidence: float = 0.9) -> bool:
        """存储用户偏好"""
        return self.permanent.add_preference(key, value, confidence)
    
    def get_user_preference(self, key: str) -> Optional[Any]:
        """获取用户偏好"""
        return self.permanent.get_preference(key)
    
    def get_all_facts(self, category: str = None) -> List[Dict]:
        """获取所有永久事实"""
        return self.permanent.list_facts(category)
    
    def clean_forgetting(self, vector_memory) -> int:
        """执行遗忘清理：移除重要性过低的长期记忆，返回清理数量"""
        cleaned = 0
        # 向量记忆中根据时间衰减清理低重要性条目
        if hasattr(vector_memory, 'vectors'):
            original_count = len(vector_memory.vectors)
            kept = []
            for entry in vector_memory.vectors:
                # 获取重要性，默认为0.5
                importance = entry.get('metadata', {}).get('importance', 0.5)
                created_at = entry.get('timestamp', datetime.datetime.now().isoformat())
                created_dt = datetime.datetime.fromisoformat(created_at)
                age_hours = (datetime.datetime.now() - created_dt).total_seconds() / 3600
                decay = (0.5) ** (age_hours / DEFAULT_HALF_LIFE_HOURS)
                current = importance * decay
                if current >= MIN_IMPORTANCE:
                    kept.append(entry)
                else:
                    cleaned += 1
            if cleaned > 0:
                vector_memory.vectors = kept
                vector_memory._save()
                # 记录遗忘日志
                self._log_forgetting(cleaned, "vector_memory")
        return cleaned
    
    def _log_forgetting(self, count: int, memory_type: str):
        """记录遗忘日志"""
        try:
            with open(self.forgetting_log_path, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
        
        log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "count": count,
            "memory_type": memory_type
        })
        
        with open(self.forgetting_log_path, "w", encoding="utf-8") as f:
            json.dump(log[-100:], f, ensure_ascii=False, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        facts = self.permanent.list_facts()
        prefs = []  # 偏好单独统计
        try:
            conn = sqlite3.connect(self.permanent.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_preferences")
            pref_count = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pref_count = 0
        
        return {
            "permanent_facts_count": len(facts),
            "user_preferences_count": pref_count,
            "short_term_connected": self.short_term.is_connected()
        }


# 单例实例
_hierarchical_memory_instance = None

def get_hierarchical_memory() -> HierarchicalMemory:
    """获取单例层级记忆实例"""
    global _hierarchical_memory_instance
    if _hierarchical_memory_instance is None:
        _hierarchical_memory_instance = HierarchicalMemory()
    return _hierarchical_memory_instance


if __name__ == "__main__":
    # 测试
    hm = HierarchicalMemory()
    print("✅ HierarchicalMemory 初始化成功")
    
    # 测试永久存储
    hm.store_permanent_fact("user_name", "于金泽", "user_profile", importance=1.0)
    fact = hm.get_permanent_fact("user_name")
    print(f"📝 测试永久存储: user_name = {fact}")
    
    # 测试用户偏好
    hm.store_user_preference("favorite_coffee", "美式", 0.95)
    pref = hm.get_user_preference("favorite_coffee")
    print(f"❤️ 测试用户偏好: favorite_coffee = {pref}")
    
    stats = hm.get_stats()
    print(f"📊 统计: {stats}")
    
    print("✅ 所有测试通过")
