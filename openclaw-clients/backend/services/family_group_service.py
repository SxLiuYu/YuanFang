"""
家庭群组服务
支持家庭创建/加入、成员管理、权限控制、数据共享、家庭公告、成员位置查看
"""

import logging
import secrets
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

from db_helper import DatabaseHelper
from api_response import ApiResponse

logger = logging.getLogger(__name__)

DB_PATH = 'family_group.db'
db = DatabaseHelper(DB_PATH)


class FamilyGroupService:
    """家庭群组服务类"""

    ROLES = {
        'owner': {'level': 100, 'name': '群主', 'permissions': ['all']},
        'admin': {'level': 50, 'name': '管理员', 'permissions': ['manage_members', 'share', 'announce', 'view_location']},
        'member': {'level': 10, 'name': '成员', 'permissions': ['share', 'view_location']}
    }

    PERMISSIONS = {
        'all': '全部权限',
        'manage_members': '管理成员',
        'share': '分享数据',
        'announce': '发布公告',
        'view_location': '查看位置'
    }

    def __init__(self, db_path: str = DB_PATH):
        self.db = DatabaseHelper(db_path)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        if not self.db.table_exists('families'):
            self.db.create_table('families', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                description TEXT,
                avatar TEXT,
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')

        if not self.db.table_exists('family_members'):
            self.db.create_table('family_members', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                nickname TEXT,
                avatar TEXT,
                permissions TEXT DEFAULT '[]',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP,
                UNIQUE(family_id, user_id)
            ''')

        if not self.db.table_exists('shared_items'):
            self.db.create_table('shared_items', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT,
                item_data TEXT,
                shared_by TEXT NOT NULL,
                permissions TEXT DEFAULT '["view"]',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')

        if not self.db.table_exists('family_announcements'):
            self.db.create_table('family_announcements', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                priority TEXT DEFAULT 'normal',
                pinned BOOLEAN DEFAULT 0,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            ''')

        if not self.db.table_exists('member_locations'):
            self.db.create_table('member_locations', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                address TEXT,
                battery_level INTEGER,
                is_sharing BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(family_id, user_id)
            ''')

        if not self.db.table_exists('family_invitations'):
            self.db.create_table('family_invitations', '''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                invite_code TEXT NOT NULL,
                invited_by TEXT NOT NULL,
                invited_user_id TEXT,
                status TEXT DEFAULT 'pending',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')

    def _generate_id(self, prefix: str = 'FAM') -> str:
        """生成唯一ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(4).upper()
        return f"{prefix}_{timestamp}_{random_part}"

    def _generate_invite_code(self) -> str:
        """生成邀请码"""
        return secrets.token_urlsafe(8).upper()

    def _has_permission(self, user_role: str, permission: str) -> bool:
        """检查权限"""
        role_info = self.ROLES.get(user_role, self.ROLES['member'])
        if 'all' in role_info['permissions']:
            return True
        return permission in role_info['permissions']

    def create_family(self, name: str, creator_id: str, description: str = None, 
                      avatar: str = None, settings: dict = None) -> Dict[str, Any]:
        """创建家庭"""
        family_id = self._generate_id('FAM')
        invite_code = self._generate_invite_code()

        self.db.insert('families', {
            'family_id': family_id,
            'name': name,
            'creator_id': creator_id,
            'invite_code': invite_code,
            'description': description or '',
            'avatar': avatar or '',
            'settings': json.dumps(settings or {}, ensure_ascii=False),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })

        self.db.insert('family_members', {
            'family_id': family_id,
            'user_id': creator_id,
            'role': 'owner',
            'nickname': '',
            'permissions': json.dumps(['all'], ensure_ascii=False),
            'joined_at': datetime.now(),
            'last_active_at': datetime.now()
        })

        logger.info(f"家庭创建成功: {family_id} by {creator_id}")

        return {
            'success': True,
            'family_id': family_id,
            'invite_code': invite_code,
            'name': name
        }

    def join_family(self, invite_code: str, user_id: str, nickname: str = None) -> Dict[str, Any]:
        """加入家庭"""
        family = self.db.fetch_one(
            "SELECT * FROM families WHERE invite_code = ?", 
            (invite_code,)
        )

        if not family:
            return {'success': False, 'error': '邀请码无效'}

        existing = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family['family_id'], user_id)
        )

        if existing:
            return {'success': False, 'error': '已经是家庭成员'}

        self.db.insert('family_members', {
            'family_id': family['family_id'],
            'user_id': user_id,
            'role': 'member',
            'nickname': nickname or '',
            'permissions': json.dumps(['share', 'view_location'], ensure_ascii=False),
            'joined_at': datetime.now(),
            'last_active_at': datetime.now()
        })

        member_count = self.db.count('family_members', 'family_id = ?', (family['family_id'],))

        logger.info(f"用户 {user_id} 加入家庭 {family['family_id']}")

        return {
            'success': True,
            'family_id': family['family_id'],
            'family_name': family['name'],
            'member_count': member_count
        }

    def get_family_info(self, family_id: str, user_id: str = None) -> Dict[str, Any]:
        """获取家庭信息"""
        family = self.db.fetch_one(
            "SELECT * FROM families WHERE family_id = ?", 
            (family_id,)
        )

        if not family:
            return {'success': False, 'error': '家庭不存在'}

        member_count = self.db.count('family_members', 'family_id = ?', (family_id,))

        result = {
            'success': True,
            'family': {
                'family_id': family['family_id'],
                'name': family['name'],
                'description': family['description'],
                'avatar': family['avatar'],
                'creator_id': family['creator_id'],
                'invite_code': family['invite_code'],
                'member_count': member_count,
                'created_at': family['created_at'],
                'settings': json.loads(family['settings'] or '{}')
            }
        }

        if user_id:
            member = self.db.fetch_one(
                "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
                (family_id, user_id)
            )
            result['my_role'] = member['role'] if member else None

        return result

    def get_members(self, family_id: str) -> Dict[str, Any]:
        """获取成员列表"""
        members = self.db.fetch_all(
            '''SELECT fm.*, 
                       ml.latitude, ml.longitude, ml.address, ml.battery_level,
                       ml.is_sharing as location_sharing, ml.updated_at as location_updated_at
                FROM family_members fm
                LEFT JOIN member_locations ml ON fm.family_id = ml.family_id AND fm.user_id = ml.user_id
                WHERE fm.family_id = ?
                ORDER BY 
                    CASE fm.role 
                        WHEN 'owner' THEN 1 
                        WHEN 'admin' THEN 2 
                        ELSE 3 
                    END,
                    fm.joined_at''',
            (family_id,)
        )

        result = []
        for m in members:
            member_info = {
                'user_id': m['user_id'],
                'role': m['role'],
                'role_name': self.ROLES.get(m['role'], {}).get('name', '成员'),
                'nickname': m['nickname'],
                'avatar': m['avatar'],
                'joined_at': m['joined_at'],
                'last_active_at': m['last_active_at'],
                'permissions': json.loads(m['permissions'] or '[]')
            }

            if m['location_sharing'] and m['latitude']:
                member_info['location'] = {
                    'latitude': m['latitude'],
                    'longitude': m['longitude'],
                    'address': m['address'],
                    'battery_level': m['battery_level'],
                    'updated_at': m['location_updated_at']
                }
            else:
                member_info['location'] = None

            result.append(member_info)

        return {
            'success': True,
            'family_id': family_id,
            'members': result,
            'total': len(result)
        }

    def update_member_role(self, family_id: str, user_id: str, new_role: str, 
                           operator_id: str) -> Dict[str, Any]:
        """更新成员角色"""
        operator = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, operator_id)
        )

        if not operator:
            return {'success': False, 'error': '无权限'}

        if not self._has_permission(operator['role'], 'manage_members'):
            return {'success': False, 'error': '无权限'}

        if new_role not in self.ROLES:
            return {'success': False, 'error': '无效角色'}

        target = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not target:
            return {'success': False, 'error': '成员不存在'}

        if target['role'] == 'owner':
            return {'success': False, 'error': '不能修改群主角色'}

        operator_level = self.ROLES.get(operator['role'], {}).get('level', 0)
        target_level = self.ROLES.get(target['role'], {}).get('level', 0)

        if operator_level <= target_level:
            return {'success': False, 'error': '权限不足'}

        permissions = self.ROLES[new_role]['permissions']

        self.db.update(
            'family_members',
            {'role': new_role, 'permissions': json.dumps(permissions, ensure_ascii=False)},
            'family_id = ? AND user_id = ?',
            (family_id, user_id)
        )

        logger.info(f"成员角色更新: {user_id} -> {new_role} by {operator_id}")

        return {
            'success': True,
            'user_id': user_id,
            'new_role': new_role
        }

    def remove_member(self, family_id: str, user_id: str, operator_id: str) -> Dict[str, Any]:
        """移除成员"""
        operator = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, operator_id)
        )

        if not operator:
            return {'success': False, 'error': '无权限'}

        if not self._has_permission(operator['role'], 'manage_members'):
            return {'success': False, 'error': '无权限'}

        target = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not target:
            return {'success': False, 'error': '成员不存在'}

        if target['role'] == 'owner':
            return {'success': False, 'error': '不能移除群主'}

        self.db.delete(
            'family_members',
            'family_id = ? AND user_id = ?',
            (family_id, user_id)
        )

        self.db.delete(
            'member_locations',
            'family_id = ? AND user_id = ?',
            (family_id, user_id)
        )

        logger.info(f"成员移除: {user_id} from {family_id} by {operator_id}")

        return {'success': True}

    def leave_family(self, family_id: str, user_id: str) -> Dict[str, Any]:
        """退出家庭"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        if member['role'] == 'owner':
            member_count = self.db.count('family_members', 'family_id = ?', (family_id,))
            if member_count > 1:
                return {'success': False, 'error': '群主需要先转让或解散家庭'}

            self.db.delete('families', 'family_id = ?', (family_id,))
            self.db.delete('family_members', 'family_id = ?', (family_id,))
            self.db.delete('shared_items', 'family_id = ?', (family_id,))
            self.db.delete('family_announcements', 'family_id = ?', (family_id,))
            self.db.delete('member_locations', 'family_id = ?', (family_id,))
        else:
            self.db.delete('family_members', 'family_id = ? AND user_id = ?', (family_id, user_id))
            self.db.delete('member_locations', 'family_id = ? AND user_id = ?', (family_id, user_id))

        logger.info(f"用户 {user_id} 退出家庭 {family_id}")

        return {'success': True}

    def share_item(self, family_id: str, item_type: str, item_id: str, item_name: str,
                   shared_by: str, item_data: dict = None, permissions: list = None,
                   expires_at: datetime = None) -> Dict[str, Any]:
        """分享数据"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, shared_by)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        if not self._has_permission(member['role'], 'share'):
            return {'success': False, 'error': '无分享权限'}

        share_id = self._generate_id('SHR')

        self.db.insert('shared_items', {
            'family_id': family_id,
            'item_type': item_type,
            'item_id': item_id,
            'item_name': item_name,
            'item_data': json.dumps(item_data or {}, ensure_ascii=False),
            'shared_by': shared_by,
            'permissions': json.dumps(permissions or ['view'], ensure_ascii=False),
            'expires_at': expires_at,
            'created_at': datetime.now()
        })

        logger.info(f"数据分享: {item_type}/{item_id} in {family_id} by {shared_by}")

        return {
            'success': True,
            'share_id': share_id,
            'item_type': item_type,
            'item_id': item_id
        }

    def get_shared_items(self, family_id: str, item_type: str = None, 
                         user_id: str = None) -> Dict[str, Any]:
        """获取分享列表"""
        sql = '''SELECT si.*, fm.nickname as shared_by_name, fm.avatar as shared_by_avatar
                 FROM shared_items si
                 LEFT JOIN family_members fm ON si.shared_by = fm.user_id AND si.family_id = fm.family_id
                 WHERE si.family_id = ?'''
        params = [family_id]

        if item_type:
            sql += ' AND si.item_type = ?'
            params.append(item_type)

        sql += ' AND (si.expires_at IS NULL OR si.expires_at > ?) ORDER BY si.created_at DESC'
        params.append(datetime.now())

        items = self.db.fetch_all(sql, tuple(params))

        result = []
        for item in items:
            result.append({
                'id': item['id'],
                'item_type': item['item_type'],
                'item_id': item['item_id'],
                'item_name': item['item_name'],
                'item_data': json.loads(item['item_data'] or '{}'),
                'shared_by': item['shared_by'],
                'shared_by_name': item['shared_by_name'],
                'permissions': json.loads(item['permissions'] or '[]'),
                'created_at': item['created_at'],
                'expires_at': item['expires_at']
            })

        return {
            'success': True,
            'family_id': family_id,
            'items': result,
            'total': len(result)
        }

    def delete_shared_item(self, family_id: str, item_id: int, user_id: str) -> Dict[str, Any]:
        """删除分享"""
        item = self.db.fetch_one(
            "SELECT * FROM shared_items WHERE id = ? AND family_id = ?",
            (item_id, family_id)
        )

        if not item:
            return {'success': False, 'error': '分享不存在'}

        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '无权限'}

        if item['shared_by'] != user_id and not self._has_permission(member['role'], 'manage_members'):
            return {'success': False, 'error': '无权限'}

        self.db.delete('shared_items', 'id = ?', (item_id,))

        return {'success': True}

    def create_announcement(self, family_id: str, title: str, content: str,
                            created_by: str, priority: str = 'normal', 
                            pinned: bool = False, expires_at: datetime = None) -> Dict[str, Any]:
        """创建公告"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, created_by)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        if not self._has_permission(member['role'], 'announce'):
            return {'success': False, 'error': '无发布公告权限'}

        announcement_id = self.db.insert('family_announcements', {
            'family_id': family_id,
            'title': title,
            'content': content,
            'priority': priority,
            'pinned': pinned,
            'created_by': created_by,
            'expires_at': expires_at,
            'created_at': datetime.now()
        })

        logger.info(f"公告创建: {announcement_id} in {family_id}")

        return {
            'success': True,
            'announcement_id': announcement_id,
            'title': title
        }

    def get_announcements(self, family_id: str, include_expired: bool = False) -> Dict[str, Any]:
        """获取公告列表"""
        sql = '''SELECT a.*, fm.nickname as created_by_name
                 FROM family_announcements a
                 LEFT JOIN family_members fm ON a.created_by = fm.user_id AND a.family_id = fm.family_id
                 WHERE a.family_id = ?'''
        params = [family_id]

        if not include_expired:
            sql += ' AND (a.expires_at IS NULL OR a.expires_at > ?)'
            params.append(datetime.now())

        sql += ' ORDER BY a.pinned DESC, a.created_at DESC'

        items = self.db.fetch_all(sql, tuple(params))

        result = []
        for item in items:
            result.append({
                'id': item['id'],
                'title': item['title'],
                'content': item['content'],
                'priority': item['priority'],
                'pinned': bool(item['pinned']),
                'created_by': item['created_by'],
                'created_by_name': item['created_by_name'],
                'created_at': item['created_at'],
                'expires_at': item['expires_at']
            })

        return {
            'success': True,
            'family_id': family_id,
            'announcements': result,
            'total': len(result)
        }

    def delete_announcement(self, family_id: str, announcement_id: int, 
                            user_id: str) -> Dict[str, Any]:
        """删除公告"""
        announcement = self.db.fetch_one(
            "SELECT * FROM family_announcements WHERE id = ? AND family_id = ?",
            (announcement_id, family_id)
        )

        if not announcement:
            return {'success': False, 'error': '公告不存在'}

        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '无权限'}

        if announcement['created_by'] != user_id and not self._has_permission(member['role'], 'announce'):
            return {'success': False, 'error': '无权限'}

        self.db.delete('family_announcements', 'id = ?', (announcement_id,))

        return {'success': True}

    def update_location(self, family_id: str, user_id: str, latitude: float, 
                        longitude: float, address: str = None, 
                        battery_level: int = None) -> Dict[str, Any]:
        """更新位置"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        existing = self.db.fetch_one(
            "SELECT * FROM member_locations WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if existing:
            self.db.update(
                'member_locations',
                {
                    'latitude': latitude,
                    'longitude': longitude,
                    'address': address,
                    'battery_level': battery_level,
                    'updated_at': datetime.now()
                },
                'family_id = ? AND user_id = ?',
                (family_id, user_id)
            )
        else:
            self.db.insert('member_locations', {
                'family_id': family_id,
                'user_id': user_id,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'battery_level': battery_level,
                'is_sharing': True,
                'updated_at': datetime.now()
            })

        return {
            'success': True,
            'latitude': latitude,
            'longitude': longitude
        }

    def toggle_location_sharing(self, family_id: str, user_id: str, 
                                 is_sharing: bool) -> Dict[str, Any]:
        """切换位置共享"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        existing = self.db.fetch_one(
            "SELECT * FROM member_locations WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if existing:
            self.db.update(
                'member_locations',
                {'is_sharing': is_sharing, 'updated_at': datetime.now()},
                'family_id = ? AND user_id = ?',
                (family_id, user_id)
            )
        else:
            self.db.insert('member_locations', {
                'family_id': family_id,
                'user_id': user_id,
                'is_sharing': is_sharing,
                'updated_at': datetime.now()
            })

        return {
            'success': True,
            'is_sharing': is_sharing
        }

    def get_member_locations(self, family_id: str, user_id: str) -> Dict[str, Any]:
        """获取成员位置"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        if not self._has_permission(member['role'], 'view_location'):
            return {'success': False, 'error': '无查看位置权限'}

        locations = self.db.fetch_all(
            '''SELECT ml.*, fm.nickname, fm.avatar, fm.role
                FROM member_locations ml
                JOIN family_members fm ON ml.family_id = fm.family_id AND ml.user_id = fm.user_id
                WHERE ml.family_id = ? AND ml.is_sharing = 1''',
            (family_id,)
        )

        result = []
        for loc in locations:
            result.append({
                'user_id': loc['user_id'],
                'nickname': loc['nickname'],
                'avatar': loc['avatar'],
                'role': loc['role'],
                'latitude': loc['latitude'],
                'longitude': loc['longitude'],
                'address': loc['address'],
                'battery_level': loc['battery_level'],
                'updated_at': loc['updated_at']
            })

        return {
            'success': True,
            'family_id': family_id,
            'locations': result,
            'total': len(result)
        }

    def get_user_families(self, user_id: str) -> Dict[str, Any]:
        """获取用户所在的家庭列表"""
        families = self.db.fetch_all(
            '''SELECT f.*, fm.role, fm.nickname, fm.joined_at as my_joined_at
                FROM families f
                JOIN family_members fm ON f.family_id = fm.family_id
                WHERE fm.user_id = ?
                ORDER BY fm.joined_at DESC''',
            (user_id,)
        )

        result = []
        for f in families:
            member_count = self.db.count('family_members', 'family_id = ?', (f['family_id'],))
            result.append({
                'family_id': f['family_id'],
                'name': f['name'],
                'description': f['description'],
                'avatar': f['avatar'],
                'creator_id': f['creator_id'],
                'my_role': f['role'],
                'my_nickname': f['nickname'],
                'member_count': member_count,
                'joined_at': f['my_joined_at'],
                'created_at': f['created_at']
            })

        return {
            'success': True,
            'families': result,
            'total': len(result)
        }

    def update_family_info(self, family_id: str, user_id: str, 
                           name: str = None, description: str = None,
                           avatar: str = None, settings: dict = None) -> Dict[str, Any]:
        """更新家庭信息"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member:
            return {'success': False, 'error': '不是家庭成员'}

        if member['role'] not in ['owner', 'admin']:
            return {'success': False, 'error': '无权限'}

        update_data = {'updated_at': datetime.now()}
        if name:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if avatar is not None:
            update_data['avatar'] = avatar
        if settings:
            update_data['settings'] = json.dumps(settings, ensure_ascii=False)

        self.db.update('families', update_data, 'family_id = ?', (family_id,))

        return {'success': True}

    def regenerate_invite_code(self, family_id: str, user_id: str) -> Dict[str, Any]:
        """重新生成邀请码"""
        member = self.db.fetch_one(
            "SELECT * FROM family_members WHERE family_id = ? AND user_id = ?",
            (family_id, user_id)
        )

        if not member or member['role'] != 'owner':
            return {'success': False, 'error': '只有群主可以重新生成邀请码'}

        new_code = self._generate_invite_code()

        self.db.update(
            'families',
            {'invite_code': new_code, 'updated_at': datetime.now()},
            'family_id = ?',
            (family_id,)
        )

        return {
            'success': True,
            'invite_code': new_code
        }


app = Flask(__name__)
CORS(app)

service = FamilyGroupService()


@app.route('/api/v1/family/create', methods=['POST'])
def create_family():
    """创建家庭"""
    data = request.json
    result = service.create_family(
        name=data.get('name'),
        creator_id=data.get('user_id'),
        description=data.get('description'),
        avatar=data.get('avatar'),
        settings=data.get('settings')
    )
    if result.get('success'):
        return ApiResponse.created(result, '家庭创建成功')
    return ApiResponse.bad_request(result.get('error', '创建失败'))


@app.route('/api/v1/family/join', methods=['POST'])
def join_family():
    """加入家庭"""
    data = request.json
    result = service.join_family(
        invite_code=data.get('invite_code'),
        user_id=data.get('user_id'),
        nickname=data.get('nickname')
    )
    if result.get('success'):
        return ApiResponse.success(result, '加入成功')
    return ApiResponse.bad_request(result.get('error', '加入失败'))


@app.route('/api/v1/family/<family_id>', methods=['GET'])
def get_family(family_id):
    """获取家庭信息"""
    user_id = request.args.get('user_id')
    result = service.get_family_info(family_id, user_id)
    if result.get('success'):
        return ApiResponse.success(result.get('family'))
    return ApiResponse.not_found(result.get('error', '家庭不存在'))


@app.route('/api/v1/family/members', methods=['GET'])
def get_members():
    """获取成员列表"""
    family_id = request.args.get('family_id')
    if not family_id:
        return ApiResponse.bad_request('缺少 family_id')
    result = service.get_members(family_id)
    return ApiResponse.success(result.get('members'), '获取成功')


@app.route('/api/v1/family/member/role', methods=['PUT'])
def update_member_role():
    """更新成员角色"""
    data = request.json
    result = service.update_member_role(
        family_id=data.get('family_id'),
        user_id=data.get('user_id'),
        new_role=data.get('role'),
        operator_id=data.get('operator_id')
    )
    if result.get('success'):
        return ApiResponse.success(result, '角色更新成功')
    return ApiResponse.forbidden(result.get('error', '更新失败'))


@app.route('/api/v1/family/member/remove', methods=['DELETE'])
def remove_member():
    """移除成员"""
    data = request.json
    result = service.remove_member(
        family_id=data.get('family_id'),
        user_id=data.get('user_id'),
        operator_id=data.get('operator_id')
    )
    if result.get('success'):
        return ApiResponse.success(message='成员已移除')
    return ApiResponse.forbidden(result.get('error', '移除失败'))


@app.route('/api/v1/family/leave', methods=['POST'])
def leave_family():
    """退出家庭"""
    data = request.json
    result = service.leave_family(
        family_id=data.get('family_id'),
        user_id=data.get('user_id')
    )
    if result.get('success'):
        return ApiResponse.success(message='已退出家庭')
    return ApiResponse.bad_request(result.get('error', '退出失败'))


@app.route('/api/v1/family/share', methods=['POST'])
def share_item():
    """分享数据"""
    data = request.json
    result = service.share_item(
        family_id=data.get('family_id'),
        item_type=data.get('item_type'),
        item_id=data.get('item_id'),
        item_name=data.get('item_name'),
        shared_by=data.get('user_id'),
        item_data=data.get('item_data'),
        permissions=data.get('permissions'),
        expires_at=data.get('expires_at')
    )
    if result.get('success'):
        return ApiResponse.created(result, '分享成功')
    return ApiResponse.forbidden(result.get('error', '分享失败'))


@app.route('/api/v1/family/shared', methods=['GET'])
def get_shared():
    """获取分享列表"""
    family_id = request.args.get('family_id')
    item_type = request.args.get('item_type')
    user_id = request.args.get('user_id')
    result = service.get_shared_items(family_id, item_type, user_id)
    return ApiResponse.success(result.get('items'))


@app.route('/api/v1/family/shared/<int:item_id>', methods=['DELETE'])
def delete_shared(item_id):
    """删除分享"""
    data = request.json
    result = service.delete_shared_item(
        family_id=data.get('family_id'),
        item_id=item_id,
        user_id=data.get('user_id')
    )
    if result.get('success'):
        return ApiResponse.success(message='已取消分享')
    return ApiResponse.forbidden(result.get('error', '删除失败'))


@app.route('/api/v1/family/announcement', methods=['POST'])
def create_announcement():
    """创建公告"""
    data = request.json
    result = service.create_announcement(
        family_id=data.get('family_id'),
        title=data.get('title'),
        content=data.get('content'),
        created_by=data.get('user_id'),
        priority=data.get('priority', 'normal'),
        pinned=data.get('pinned', False),
        expires_at=data.get('expires_at')
    )
    if result.get('success'):
        return ApiResponse.created(result, '公告发布成功')
    return ApiResponse.forbidden(result.get('error', '发布失败'))


@app.route('/api/v1/family/announcements', methods=['GET'])
def get_announcements():
    """获取公告列表"""
    family_id = request.args.get('family_id')
    include_expired = request.args.get('include_expired', 'false').lower() == 'true'
    result = service.get_announcements(family_id, include_expired)
    return ApiResponse.success(result.get('announcements'))


@app.route('/api/v1/family/announcement/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    """删除公告"""
    data = request.json
    result = service.delete_announcement(
        family_id=data.get('family_id'),
        announcement_id=announcement_id,
        user_id=data.get('user_id')
    )
    if result.get('success'):
        return ApiResponse.success(message='公告已删除')
    return ApiResponse.forbidden(result.get('error', '删除失败'))


@app.route('/api/v1/family/location/update', methods=['POST'])
def update_location():
    """更新位置"""
    data = request.json
    result = service.update_location(
        family_id=data.get('family_id'),
        user_id=data.get('user_id'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        address=data.get('address'),
        battery_level=data.get('battery_level')
    )
    if result.get('success'):
        return ApiResponse.success(message='位置已更新')
    return ApiResponse.bad_request(result.get('error', '更新失败'))


@app.route('/api/v1/family/location/toggle', methods=['POST'])
def toggle_location():
    """切换位置共享"""
    data = request.json
    result = service.toggle_location_sharing(
        family_id=data.get('family_id'),
        user_id=data.get('user_id'),
        is_sharing=data.get('is_sharing', True)
    )
    if result.get('success'):
        return ApiResponse.success(result)
    return ApiResponse.bad_request(result.get('error', '切换失败'))


@app.route('/api/v1/family/locations', methods=['GET'])
def get_locations():
    """获取成员位置"""
    family_id = request.args.get('family_id')
    user_id = request.args.get('user_id')
    result = service.get_member_locations(family_id, user_id)
    if result.get('success'):
        return ApiResponse.success(result.get('locations'))
    return ApiResponse.forbidden(result.get('error', '获取失败'))


@app.route('/api/v1/family/list', methods=['GET'])
def get_user_families():
    """获取用户家庭列表"""
    user_id = request.args.get('user_id')
    if not user_id:
        return ApiResponse.bad_request('缺少 user_id')
    result = service.get_user_families(user_id)
    return ApiResponse.success(result.get('families'))


@app.route('/api/v1/family/update', methods=['PUT'])
def update_family():
    """更新家庭信息"""
    data = request.json
    result = service.update_family_info(
        family_id=data.get('family_id'),
        user_id=data.get('user_id'),
        name=data.get('name'),
        description=data.get('description'),
        avatar=data.get('avatar'),
        settings=data.get('settings')
    )
    if result.get('success'):
        return ApiResponse.success(message='更新成功')
    return ApiResponse.forbidden(result.get('error', '更新失败'))


@app.route('/api/v1/family/invite-code/regenerate', methods=['POST'])
def regenerate_invite():
    """重新生成邀请码"""
    data = request.json
    result = service.regenerate_invite_code(
        family_id=data.get('family_id'),
        user_id=data.get('user_id')
    )
    if result.get('success'):
        return ApiResponse.success(result)
    return ApiResponse.forbidden(result.get('error', '生成失败'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)