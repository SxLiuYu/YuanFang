#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw - 家庭群组协作服务
支持群组管理、位置共享、共享日历

Author: 于金泽
Version: 1.0.0
"""

import json
import uuid
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

class FamilyGroupCreate(BaseModel):
    name: str
    owner_id: str

class FamilyGroupUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class FamilyMemberAdd(BaseModel):
    group_id: str
    user_id: str
    name: str
    role: str = "member"

class LocationShare(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    accuracy: Optional[float] = None

class SharedScheduleCreate(BaseModel):
    group_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    assignees: List[str] = []
    reminders: List[int] = []

class FamilyGroup(BaseModel):
    id: str
    name: str
    owner_id: str
    members: List[Dict[str, Any]] = []
    invite_code: str
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class FamilyMember(BaseModel):
    user_id: str
    name: str
    role: str
    avatar: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    last_active: Optional[datetime] = None

class SharedSchedule(BaseModel):
    id: str
    group_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    assignees: List[str] = []
    reminders: List[int] = []
    status: str = "pending"
    created_by: str
    created_at: datetime

# ═══════════════════════════════════════════════════════════════
# 家庭服务类
# ═══════════════════════════════════════════════════════════════

class FamilyService:
    """家庭群组协作服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent.parent / "data" / "family.db")
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 家庭群组表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                invite_code TEXT UNIQUE,
                settings TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 群组成员表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                avatar TEXT,
                last_active DATETIME,
                FOREIGN KEY (group_id) REFERENCES family_groups(id),
                UNIQUE(group_id, user_id)
            )
        """)
        
        # 位置共享表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                accuracy REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES family_groups(id)
            )
        """)
        
        # 共享日程表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_schedules (
                id TEXT PRIMARY KEY,
                group_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                assignees TEXT,
                reminders TEXT,
                status TEXT DEFAULT 'pending',
                created_by TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES family_groups(id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_group ON family_members(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_user ON family_members(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location_group ON location_shares(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_group ON shared_schedules(group_id)")
        
        conn.commit()
        conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 群组管理
    # ═══════════════════════════════════════════════════════════════
    
    async def create_group(self, request: FamilyGroupCreate) -> Dict[str, Any]:
        """创建家庭群组"""
        group_id = str(uuid.uuid4())
        invite_code = self._generate_invite_code()
        now = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建群组
            cursor.execute("""
                INSERT INTO family_groups (id, name, owner_id, invite_code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (group_id, request.name, request.owner_id, invite_code, now, now))
            
            # 添加创建者为管理员
            cursor.execute("""
                INSERT INTO family_members (group_id, user_id, name, role, last_active)
                VALUES (?, ?, ?, 'owner', ?)
            """, (group_id, request.owner_id, request.owner_id, now))
            
            conn.commit()
            
            return {
                "success": True,
                "group_id": group_id,
                "invite_code": invite_code,
                "message": f"家庭群组 '{request.name}' 创建成功"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"创建群组失败: {e}")
            return {"success": False, "message": f"创建失败: {str(e)}"}
        finally:
            conn.close()
    
    async def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """获取群组详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取群组信息
            cursor.execute("""
                SELECT id, name, owner_id, invite_code, settings, created_at, updated_at
                FROM family_groups WHERE id = ?
            """, (group_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            group = {
                "id": row[0],
                "name": row[1],
                "owner_id": row[2],
                "invite_code": row[3],
                "settings": json.loads(row[4]) if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6],
                "members": []
            }
            
            # 获取成员列表
            cursor.execute("""
                SELECT user_id, name, role, avatar, last_active
                FROM family_members WHERE group_id = ?
            """, (group_id,))
            
            members = []
            for member_row in cursor.fetchall():
                members.append({
                    "user_id": member_row[0],
                    "name": member_row[1],
                    "role": member_row[2],
                    "avatar": member_row[3],
                    "last_active": member_row[4]
                })
            
            group["members"] = members
            return group
            
        finally:
            conn.close()
    
    async def update_group(self, group_id: str, request: FamilyGroupUpdate) -> Dict[str, Any]:
        """更新群组信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if request.name:
                updates.append("name = ?")
                params.append(request.name)
            
            if request.settings:
                updates.append("settings = ?")
                params.append(json.dumps(request.settings, ensure_ascii=False))
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now())
                params.append(group_id)
                
                cursor.execute(f"""
                    UPDATE family_groups 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
            
            return {"success": True, "message": "群组信息更新成功"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新群组失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
        finally:
            conn.close()
    
    async def delete_group(self, group_id: str, owner_id: str) -> Dict[str, Any]:
        """删除群组"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证是否为群主
            cursor.execute("SELECT owner_id FROM family_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"success": False, "message": "群组不存在"}
            
            if row[0] != owner_id:
                return {"success": False, "message": "只有群主可以删除群组"}
            
            # 删除相关数据
            cursor.execute("DELETE FROM shared_schedules WHERE group_id = ?", (group_id,))
            cursor.execute("DELETE FROM location_shares WHERE group_id = ?", (group_id,))
            cursor.execute("DELETE FROM family_members WHERE group_id = ?", (group_id,))
            cursor.execute("DELETE FROM family_groups WHERE id = ?", (group_id,))
            
            conn.commit()
            return {"success": True, "message": "群组已删除"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"删除群组失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 成员管理
    # ═══════════════════════════════════════════════════════════════
    
    async def add_member(self, request: FamilyMemberAdd) -> Dict[str, Any]:
        """添加成员"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查群组是否存在
            cursor.execute("SELECT name FROM family_groups WHERE id = ?", (request.group_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "群组不存在"}
            
            # 检查成员是否已存在
            cursor.execute("""
                SELECT user_id FROM family_members 
                WHERE group_id = ? AND user_id = ?
            """, (request.group_id, request.user_id))
            
            if cursor.fetchone():
                return {"success": False, "message": "成员已存在"}
            
            # 添加成员
            cursor.execute("""
                INSERT INTO family_members (group_id, user_id, name, role, last_active)
                VALUES (?, ?, ?, ?, ?)
            """, (request.group_id, request.user_id, request.name, request.role, datetime.now()))
            
            conn.commit()
            return {"success": True, "message": f"成员 '{request.name}' 添加成功"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"添加成员失败: {e}")
            return {"success": False, "message": f"添加失败: {str(e)}"}
        finally:
            conn.close()
    
    async def join_group(self, invite_code: str, user_id: str, name: str) -> Dict[str, Any]:
        """通过邀请码加入群组"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找群组
            cursor.execute("""
                SELECT id, name FROM family_groups WHERE invite_code = ?
            """, (invite_code,))
            
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "邀请码无效"}
            
            group_id, group_name = row
            
            # 检查是否已是成员
            cursor.execute("""
                SELECT user_id FROM family_members 
                WHERE group_id = ? AND user_id = ?
            """, (group_id, user_id))
            
            if cursor.fetchone():
                return {"success": False, "message": "您已是群组成员"}
            
            # 添加成员
            cursor.execute("""
                INSERT INTO family_members (group_id, user_id, name, role, last_active)
                VALUES (?, ?, ?, 'member', ?)
            """, (group_id, user_id, name, datetime.now()))
            
            conn.commit()
            return {
                "success": True,
                "group_id": group_id,
                "group_name": group_name,
                "message": f"成功加入家庭群组 '{group_name}'"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"加入群组失败: {e}")
            return {"success": False, "message": f"加入失败: {str(e)}"}
        finally:
            conn.close()
    
    async def remove_member(self, group_id: str, user_id: str, operator_id: str) -> Dict[str, Any]:
        """移除成员"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证权限
            cursor.execute("SELECT owner_id FROM family_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"success": False, "message": "群组不存在"}
            
            owner_id = row[0]
            
            # 检查操作权限
            if operator_id != owner_id and operator_id != user_id:
                return {"success": False, "message": "无权移除此成员"}
            
            # 不能移除群主
            if user_id == owner_id:
                return {"success": False, "message": "不能移除群主，请先转让群主或解散群组"}
            
            # 移除成员
            cursor.execute("""
                DELETE FROM family_members 
                WHERE group_id = ? AND user_id = ?
            """, (group_id, user_id))
            
            conn.commit()
            return {"success": True, "message": "成员已移除"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"移除成员失败: {e}")
            return {"success": False, "message": f"移除失败: {str(e)}"}
        finally:
            conn.close()
    
    async def update_member_role(self, group_id: str, user_id: str, new_role: str, operator_id: str) -> Dict[str, Any]:
        """更新成员角色"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证是否为群主
            cursor.execute("SELECT owner_id FROM family_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            
            if not row or row[0] != operator_id:
                return {"success": False, "message": "只有群主可以修改成员角色"}
            
            # 更新角色
            cursor.execute("""
                UPDATE family_members SET role = ?
                WHERE group_id = ? AND user_id = ?
            """, (new_role, group_id, user_id))
            
            conn.commit()
            return {"success": True, "message": "角色已更新"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新角色失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 位置共享
    # ═══════════════════════════════════════════════════════════════
    
    async def share_location(self, group_id: str, request: LocationShare) -> Dict[str, Any]:
        """分享位置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 验证成员身份
            cursor.execute("""
                SELECT user_id FROM family_members 
                WHERE group_id = ? AND user_id = ?
            """, (group_id, request.user_id))
            
            if not cursor.fetchone():
                return {"success": False, "message": "您不是群组成员"}
            
            # 保存位置
            cursor.execute("""
                INSERT INTO location_shares 
                (group_id, user_id, latitude, longitude, address, accuracy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (group_id, request.user_id, request.latitude, request.longitude, 
                  request.address, request.accuracy))
            
            conn.commit()
            return {"success": True, "message": "位置已分享"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"分享位置失败: {e}")
            return {"success": False, "message": f"分享失败: {str(e)}"}
        finally:
            conn.close()
    
    async def get_member_locations(self, group_id: str) -> List[Dict[str, Any]]:
        """获取成员位置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取每个成员的最新位置
            cursor.execute("""
                SELECT ls.user_id, fm.name, ls.latitude, ls.longitude, 
                       ls.address, ls.accuracy, ls.timestamp
                FROM location_shares ls
                JOIN family_members fm ON ls.user_id = fm.user_id AND ls.group_id = fm.group_id
                WHERE ls.group_id = ?
                AND ls.id IN (
                    SELECT MAX(id) FROM location_shares 
                    WHERE group_id = ? GROUP BY user_id
                )
            """, (group_id, group_id))
            
            locations = []
            for row in cursor.fetchall():
                locations.append({
                    "user_id": row[0],
                    "name": row[1],
                    "latitude": row[2],
                    "longitude": row[3],
                    "address": row[4],
                    "accuracy": row[5],
                    "timestamp": row[6]
                })
            
            return locations
            
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 共享日程
    # ═══════════════════════════════════════════════════════════════
    
    async def create_shared_schedule(self, request: SharedScheduleCreate) -> Dict[str, Any]:
        """创建共享日程"""
        schedule_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO shared_schedules 
                (id, group_id, title, description, start_time, end_time, 
                 assignees, reminders, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (schedule_id, request.group_id, request.title, request.description,
                  request.start_time, request.end_time,
                  json.dumps(request.assignees), json.dumps(request.reminders),
                  request.assignees[0] if request.assignees else ""))
            
            conn.commit()
            return {
                "success": True,
                "schedule_id": schedule_id,
                "message": f"日程 '{request.title}' 创建成功"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"创建日程失败: {e}")
            return {"success": False, "message": f"创建失败: {str(e)}"}
        finally:
            conn.close()
    
    async def get_group_schedules(self, group_id: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取群组日程"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, group_id, title, description, start_time, end_time,
                       assignees, reminders, status, created_by, created_at
                FROM shared_schedules
                WHERE group_id = ?
            """
            params = [group_id]
            
            if start_date:
                query += " AND start_time >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND start_time <= ?"
                params.append(end_date)
            
            query += " ORDER BY start_time"
            
            cursor.execute(query, params)
            
            schedules = []
            for row in cursor.fetchall():
                schedules.append({
                    "id": row[0],
                    "group_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "start_time": row[4],
                    "end_time": row[5],
                    "assignees": json.loads(row[6]) if row[6] else [],
                    "reminders": json.loads(row[7]) if row[7] else [],
                    "status": row[8],
                    "created_by": row[9],
                    "created_at": row[10]
                })
            
            return schedules
            
        finally:
            conn.close()
    
    async def update_schedule_status(self, schedule_id: str, status: str, user_id: str) -> Dict[str, Any]:
        """更新日程状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE shared_schedules SET status = ?
                WHERE id = ?
            """, (status, schedule_id))
            
            conn.commit()
            return {"success": True, "message": "日程状态已更新"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新日程状态失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════
    
    def _generate_invite_code(self) -> str:
        """生成邀请码"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所在的所有群组"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT fg.id, fg.name, fg.owner_id, fg.invite_code, 
                       fm.role, fg.created_at
                FROM family_groups fg
                JOIN family_members fm ON fg.id = fm.group_id
                WHERE fm.user_id = ?
                ORDER BY fg.created_at DESC
            """, (user_id,))
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    "id": row[0],
                    "name": row[1],
                    "owner_id": row[2],
                    "invite_code": row[3],
                    "my_role": row[4],
                    "created_at": row[5]
                })
            
            return groups
            
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════
# 服务实例
# ═══════════════════════════════════════════════════════════════

family_service = FamilyService()