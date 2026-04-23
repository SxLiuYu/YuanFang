#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""购物清单服务 - SQLite持久化版本"""
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ShoppingService:
    """购物清单服务"""
    
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
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit TEXT,
                category TEXT DEFAULT 'other',
                checked BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE,
                quantity INTEGER DEFAULT 0,
                unit TEXT,
                updated_at TIMESTAMP
            )
        ''')
        self._conn.commit()
        logger.info("Shopping service database initialized")
    
    async def add_item(self, name: str, quantity: int = 1, category: str = "other",
                       unit: str = None, priority: int = 0, notes: str = None) -> Dict[str, Any]:
        """
        添加购物项
        
        Args:
            name: 物品名称
            quantity: 数量
            category: 分类 (food/daily/clothing/electronics/other)
            unit: 单位
            priority: 优先级 (0=普通, 1=重要, 2=紧急)
            notes: 备注
        
        Returns:
            添加的物品信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            item_id = f"item_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            now = datetime.now()
            
            c.execute('''
                INSERT INTO shopping_items 
                (item_id, name, quantity, unit, category, checked, priority, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            ''', (item_id, name, quantity, unit, category, priority, notes, now, now))
            
            conn.commit()
            
            logger.info(f"Shopping item added: {name} (ID: {item_id})")
            
            return {
                "id": item_id,
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "category": category,
                "checked": False,
                "priority": priority,
                "notes": notes,
                "created_at": now.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to add shopping item: {e}")
            return {"error": str(e)}
    
    async def get_list(self, category: str = None, checked: bool = None) -> Dict[str, Any]:
        """
        获取购物清单
        
        Args:
            category: 筛选分类（可选）
            checked: 筛选勾选状态（可选）
        
        Returns:
            购物清单
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        query = "SELECT * FROM shopping_items WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if checked is not None:
            query += " AND checked = ?"
            params.append(1 if checked else 0)
        
        query += " ORDER BY priority DESC, created_at DESC"
        
        c.execute(query, params)
        
        items = []
        for row in c.fetchall():
            items.append({
                "id": row['item_id'],
                "name": row['name'],
                "quantity": row['quantity'],
                "unit": row['unit'],
                "category": row['category'],
                "checked": bool(row['checked']),
                "priority": row['priority'],
                "notes": row['notes'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            })
        
        return {"items": items}
    
    async def check_item(self, item_id: str, checked: bool = True) -> Dict[str, Any]:
        """
        勾选/取消勾选购物项
        
        Args:
            item_id: 物品ID
            checked: 是否勾选
        
        Returns:
            更新后的物品信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE shopping_items 
            SET checked = ?, updated_at = ? 
            WHERE item_id = ?
        ''', (1 if checked else 0, datetime.now(), item_id))
        
        if c.rowcount == 0:
            return {"error": "Item not found"}
        
        conn.commit()
        
        c.execute('SELECT * FROM shopping_items WHERE item_id = ?', (item_id,))
        row = c.fetchone()
        
        if row:
            logger.info(f"Shopping item checked: {item_id} = {checked}")
            return {
                "id": row['item_id'],
                "name": row['name'],
                "quantity": row['quantity'],
                "category": row['category'],
                "checked": bool(row['checked'])
            }
        
        return {"error": "Item not found"}
    
    async def update_item(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新购物项
        
        Args:
            item_id: 物品ID
            **kwargs: 要更新的字段 (name, quantity, unit, category, priority, notes)
        
        Returns:
            更新后的物品信息
        """
        allowed_fields = ['name', 'quantity', 'unit', 'category', 'priority', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return {"error": "No valid fields to update"}
        
        updates['updated_at'] = datetime.now()
        
        conn = self._get_conn()
        c = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [item_id]
        
        c.execute(f"UPDATE shopping_items SET {set_clause} WHERE item_id = ?", values)
        
        if c.rowcount == 0:
            return {"error": "Item not found"}
        
        conn.commit()
        
        c.execute('SELECT * FROM shopping_items WHERE item_id = ?', (item_id,))
        row = c.fetchone()
        
        logger.info(f"Shopping item updated: {item_id}")
        
        return {
            "id": row['item_id'],
            "name": row['name'],
            "quantity": row['quantity'],
            "unit": row['unit'],
            "category": row['category'],
            "checked": bool(row['checked']),
            "priority": row['priority'],
            "notes": row['notes']
        }
    
    async def delete_item(self, item_id: str) -> Dict[str, Any]:
        """
        删除购物项
        
        Args:
            item_id: 物品ID
        
        Returns:
            操作结果
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM shopping_items WHERE item_id = ?', (item_id,))
        
        if c.rowcount == 0:
            return {"error": "Item not found"}
        
        conn.commit()
        
        logger.info(f"Shopping item deleted: {item_id}")
        return {"success": True, "message": f"Item {item_id} deleted"}
    
    async def clear_checked(self) -> Dict[str, Any]:
        """
        清除已勾选的项目
        
        Returns:
            操作结果
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM shopping_items WHERE checked = 1')
        deleted_count = c.rowcount
        
        conn.commit()
        
        logger.info(f"Cleared {deleted_count} checked shopping items")
        return {"success": True, "deleted_count": deleted_count}
    
    async def query_inventory(self, item_name: str) -> Dict[str, Any]:
        """
        查询库存
        
        Args:
            item_name: 物品名称
        
        Returns:
            库存信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM inventory WHERE item_name = ?', (item_name,))
        row = c.fetchone()
        
        if row:
            return {
                "item": item_name,
                "quantity": row['quantity'],
                "unit": row['unit'],
                "updated_at": row['updated_at']
            }
        
        return {"item": item_name, "quantity": 0, "unit": None}
    
    async def update_inventory(self, item_name: str, quantity: int, unit: str = None) -> Dict[str, Any]:
        """
        更新库存
        
        Args:
            item_name: 物品名称
            quantity: 数量
            unit: 单位
        
        Returns:
            更新后的库存信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        now = datetime.now()
        
        c.execute('''
            INSERT OR REPLACE INTO inventory (item_name, quantity, unit, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (item_name, quantity, unit, now))
        
        conn.commit()
        
        logger.info(f"Inventory updated: {item_name} = {quantity}")
        
        return {
            "item": item_name,
            "quantity": quantity,
            "unit": unit,
            "updated_at": now.isoformat()
        }
    
    async def get_inventory(self) -> List[Dict[str, Any]]:
        """
        获取所有库存
        
        Returns:
            库存列表
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM inventory ORDER BY item_name')
        
        inventory = []
        for row in c.fetchall():
            inventory.append({
                "item": row['item_name'],
                "quantity": row['quantity'],
                "unit": row['unit'],
                "updated_at": row['updated_at']
            })
        
        return inventory
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取购物清单统计信息
        
        Returns:
            统计信息
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM shopping_items')
        total = c.fetchone()['total']
        
        c.execute('SELECT COUNT(*) as checked FROM shopping_items WHERE checked = 1')
        checked = c.fetchone()['checked']
        
        c.execute('SELECT COUNT(*) as unchecked FROM shopping_items WHERE checked = 0')
        unchecked = c.fetchone()['unchecked']
        
        c.execute('''
            SELECT category, COUNT(*) as count 
            FROM shopping_items 
            WHERE checked = 0 
            GROUP BY category
        ''')
        by_category = {row['category']: row['count'] for row in c.fetchall()}
        
        return {
            "total": total,
            "checked": checked,
            "unchecked": unchecked,
            "by_category": by_category
        }
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None


_service_instance: Optional[ShoppingService] = None


def get_service() -> ShoppingService:
    """获取购物服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ShoppingService()
    return _service_instance


async def add_item(name: str, quantity: int = 1, category: str = "other", **kwargs) -> Dict[str, Any]:
    """添加购物项（兼容旧接口）"""
    return await get_service().add_item(name, quantity, category, **kwargs)


async def get_list(category: str = None, checked: bool = None) -> Dict[str, Any]:
    """获取购物清单（兼容旧接口）"""
    return await get_service().get_list(category, checked)


async def check_item(item_id: str, checked: bool = True) -> Dict[str, Any]:
    """勾选购物项（兼容旧接口）"""
    return await get_service().check_item(item_id, checked)


async def query_inventory(item_name: str) -> Dict[str, Any]:
    """查询库存（兼容旧接口）"""
    return await get_service().query_inventory(item_name)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        service = ShoppingService(':memory:')
        
        print("=== 购物清单服务测试 ===\n")
        
        print("1. 添加购物项...")
        item1 = await service.add_item("苹果", quantity=5, category="food", unit="个")
        print(f"   添加: {item1}")
        
        item2 = await service.add_item("牛奶", quantity=2, category="food", unit="盒", priority=1)
        print(f"   添加: {item2}")
        
        item3 = await service.add_item("洗衣液", quantity=1, category="daily", unit="瓶")
        print(f"   添加: {item3}")
        
        print("\n2. 获取购物清单...")
        shopping_list = await service.get_list()
        print(f"   共 {len(shopping_list['items'])} 项")
        for item in shopping_list['items']:
            print(f"   - [{item['category']}] {item['name']} x{item['quantity']}{item['unit'] or ''}")
        
        print("\n3. 勾选购物项...")
        result = await service.check_item(item1['id'])
        print(f"   勾选结果: {result}")
        
        print("\n4. 获取统计...")
        stats = await service.get_statistics()
        print(f"   {stats}")
        
        print("\n5. 更新库存...")
        inv = await service.update_inventory("苹果", 10, "个")
        print(f"   {inv}")
        
        print("\n6. 查询库存...")
        inv = await service.query_inventory("苹果")
        print(f"   {inv}")
        
        print("\n7. 清除已勾选项...")
        result = await service.clear_checked()
        print(f"   {result}")
        
        print("\n[OK] 测试完成！")
        
        service.close()
    
    asyncio.run(test())