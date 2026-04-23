import logging
logger = logging.getLogger(__name__)
"""
做菜服务 - 语音指导、计时器、食材采购清单
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from xiaohongshu_search_service import XiaoHongShuSearchService


class CookingService:
    """做菜服务"""
    
    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        self._conn = None
        self.xhs_service = XiaoHongShuSearchService()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        c = self._get_conn().cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT UNIQUE,
                title TEXT,
                source TEXT,
                author TEXT,
                ingredients TEXT,
                steps TEXT,
                cook_time INTEGER,
                difficulty TEXT,
                tags TEXT,
                cover_image TEXT,
                xsec_token TEXT,
                favorited BOOLEAN DEFAULT 0,
                created_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timer_name TEXT,
                duration_seconds INTEGER,
                remaining_seconds INTEGER,
                status TEXT,
                recipe_id TEXT,
                created_at TIMESTAMP
            )
        ''')
        self._conn.commit()
    
    def _get_conn(self):
        """获取数据库连接（复用连接）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    # ========== 菜谱管理 ==========
    
    def search_recipes(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        """
        搜索菜谱（从小红书）
        
        Args:
            keyword: 搜索关键词（如：红烧肉、西红柿炒蛋）
            limit: 返回数量
        
        Returns:
            搜索结果
        """
        # 使用小红书搜索
        result = self.xhs_service.search(f"{keyword} 做法", limit=limit)
        
        if result['success']:
            # 转换格式
            recipes = []
            for item in result['results']:
                recipes.append({
                    'recipe_id': item['id'],
                    'title': item['title'],
                    'author': item['author']['nickname'],
                    'cover_image': item['cover_image'],
                    'xsec_token': item['xsec_token'],
                    'url': item['url'],
                    'stats': item['stats']
                })
            
            result['recipes'] = recipes
        
        return result
    
    def get_recipe_detail(self, feed_id: str, xsec_token: str) -> Dict[str, Any]:
        """
        获取菜谱详情
        
        Args:
            feed_id: 笔记 ID
            xsec_token: 访问令牌
        
        Returns:
            菜谱详细信息
        """
        result = self.xhs_service.get_feed_detail(feed_id, xsec_token, load_comments=False)
        
        if result['success']:
            data = result.get('data', {})
            # 解析菜谱信息（根据实际返回结构调整）
            note_card = data.get('note', {}).get('noteCard', {})
            
            return {
                'success': True,
                'recipe': {
                    'title': note_card.get('displayTitle', ''),
                    'description': note_card.get('displayTitle', ''),
                    'author': note_card.get('user', {}).get('nickname', ''),
                    'images': note_card.get('imageList', []),
                    'content': data.get('note', {}).get('desc', ''),
                }
            }
        
        return result
    
    def save_recipe(self, title: str, ingredients: List[str], steps: List[str], 
                    cook_time: int = 0, difficulty: str = 'medium',
                    source: str = 'xiaohongshu', recipe_id: str = None,
                    author: str = '', cover_image: str = '', xsec_token: str = '') -> Dict[str, Any]:
        """
        保存菜谱到本地
        
        Args:
            title: 菜名
            ingredients: 食材列表
            steps: 步骤列表
            cook_time: 烹饪时间（分钟）
            difficulty: 难度（easy/medium/hard）
            source: 来源
            recipe_id: 来源 ID
            author: 作者
            cover_image: 封面图
            xsec_token: 访问令牌
        
        Returns:
            {'success': bool, 'recipe_id': str}
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        try:
            # 生成唯一 ID
            if not recipe_id:
                recipe_id = f"recipe_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            c.execute('''
                INSERT OR REPLACE INTO recipes 
                (recipe_id, title, source, author, ingredients, steps, 
                 cook_time, difficulty, tags, cover_image, xsec_token, 
                 favorited, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                recipe_id, title, source, author,
                json.dumps(ingredients, ensure_ascii=False),
                json.dumps(steps, ensure_ascii=False),
                cook_time, difficulty, '',
                cover_image, xsec_token,
                datetime.now()
            ))
            
            conn.commit()
            
            return {'success': True, 'recipe_id': recipe_id}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        finally:
            conn.close()
    
    def get_saved_recipes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取已保存的菜谱"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM recipes 
            WHERE favorited = 1 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        recipes = []
        for row in c.fetchall():
            recipes.append({
                'recipe_id': row['recipe_id'],
                'title': row['title'],
                'author': row['author'],
                'source': row['source'],
                'cook_time': row['cook_time'],
                'difficulty': row['difficulty'],
                'cover_image': row['cover_image'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return recipes
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """获取单个菜谱详情"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT * FROM recipes WHERE recipe_id = ?', (recipe_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'recipe_id': row['recipe_id'],
                'title': row['title'],
                'author': row['author'],
                'source': row['source'],
                'ingredients': json.loads(row['ingredients']),
                'steps': json.loads(row['steps']),
                'cook_time': row['cook_time'],
                'difficulty': row['difficulty'],
                'cover_image': row['cover_image']
            }
        
        return None
    
    def delete_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """删除菜谱"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM recipes WHERE recipe_id = ?', (recipe_id,))
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    # ========== 计时器管理 ==========
    
    def create_timer(self, timer_name: str, duration_seconds: int, 
                     recipe_id: str = None, step_number: int = None) -> Dict[str, Any]:
        """
        创建计时器
        
        Args:
            timer_name: 计时器名称（如：煮鸡蛋、焖饭）
            duration_seconds: 时长（秒）
            recipe_id: 关联菜谱 ID
            step_number: 关联步骤编号
        
        Returns:
            {'success': bool, 'timer_id': int}
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO timers 
            (timer_name, duration_seconds, remaining_seconds, status, 
             recipe_id, step_number, created_at)
            VALUES (?, ?, ?, 'running', ?, ?, ?)
        ''', (
            timer_name, duration_seconds, duration_seconds,
            recipe_id, step_number, datetime.now()
        ))
        
        timer_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'timer_id': timer_id}
    
    def get_timers(self, status: str = 'running') -> List[Dict[str, Any]]:
        """获取计时器列表"""
        conn = self._get_conn()
        c = conn.cursor()
        
        if status == 'all':
            c.execute('SELECT * FROM timers ORDER BY created_at DESC')
        else:
            c.execute('SELECT * FROM timers WHERE status = ? ORDER BY created_at DESC', (status,))
        
        timers = []
        for row in c.fetchall():
            timers.append({
                'timer_id': row['id'],
                'timer_name': row['timer_name'],
                'duration_seconds': row['duration_seconds'],
                'remaining_seconds': row['remaining_seconds'],
                'status': row['status'],
                'recipe_id': row['recipe_id'],
                'step_number': row['step_number'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return timers
    
    def stop_timer(self, timer_id: int) -> Dict[str, Any]:
        """停止计时器"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE timers 
            SET status = 'stopped', completed_at = ?
            WHERE id = ?
        ''', (datetime.now(), timer_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def complete_timer(self, timer_id: int) -> Dict[str, Any]:
        """完成计时器"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE timers 
            SET status = 'completed', remaining_seconds = 0, completed_at = ?
            WHERE id = ?
        ''', (datetime.now(), timer_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    # ========== 食材采购清单 ==========
    
    def add_to_shopping_list(self, item_name: str, quantity: str = '1', 
                             unit: str = '个', category: str = '其他',
                             recipe_id: str = None, note: str = '') -> Dict[str, Any]:
        """
        添加食材到采购清单
        
        Args:
            item_name: 食材名称
            quantity: 数量
            unit: 单位
            category: 分类（蔬菜/肉类/调料/其他）
            recipe_id: 关联菜谱 ID
            note: 备注
        
        Returns:
            {'success': bool, 'item_id': int}
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO shopping_list 
            (item_name, quantity, unit, category, recipe_id, purchased, note, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        ''', (item_name, quantity, unit, category, recipe_id, note, datetime.now()))
        
        item_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'item_id': item_id}
    
    def add_recipe_ingredients(self, recipe_id: str) -> Dict[str, Any]:
        """
        将菜谱的食材添加到采购清单
        
        Args:
            recipe_id: 菜谱 ID
        
        Returns:
            {'success': bool, 'added_count': int}
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return {'success': False, 'error': '菜谱不存在'}
        
        ingredients = recipe.get('ingredients', [])
        added_count = 0
        
        for ingredient in ingredients:
            # 简单解析食材（如："鸡蛋 3 个" -> 名称：鸡蛋，数量：3，单位：个）
            # 这里简化处理，实际可以更智能
            self.add_to_shopping_list(
                item_name=ingredient,
                recipe_id=recipe_id
            )
            added_count += 1
        
        return {'success': True, 'added_count': added_count}
    
    def get_shopping_list(self, purchased: bool = False) -> List[Dict[str, Any]]:
        """
        获取采购清单
        
        Args:
            purchased: 是否只显示已采购的
        
        Returns:
            采购清单列表
        """
        conn = self._get_conn()
        c = conn.cursor()
        
        if purchased:
            c.execute('''
                SELECT * FROM shopping_list 
                WHERE purchased = 1 
                ORDER BY created_at DESC
            ''')
        else:
            c.execute('''
                SELECT * FROM shopping_list 
                WHERE purchased = 0 
                ORDER BY category, created_at
            ''')
        
        items = []
        for row in c.fetchall():
            items.append({
                'item_id': row['id'],
                'item_name': row['item_name'],
                'quantity': row['quantity'],
                'unit': row['unit'],
                'category': row['category'],
                'recipe_id': row['recipe_id'],
                'purchased': row['purchased'],
                'note': row['note']
            })
        
        conn.close()
        return items
    
    def mark_purchased(self, item_id: int, purchased: bool = True) -> Dict[str, Any]:
        """标记食材已采购"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            UPDATE shopping_list 
            SET purchased = ? 
            WHERE id = ?
        ''', (1 if purchased else 0, item_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def remove_from_shopping_list(self, item_id: int) -> Dict[str, Any]:
        """从采购清单删除"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM shopping_list WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def clear_purchased_items(self) -> Dict[str, Any]:
        """清空已采购项"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('DELETE FROM shopping_list WHERE purchased = 1')
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    # ========== 语音指导 ==========
    
    def get_voice_instructions(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取菜谱的语音指导文本
        
        Args:
            recipe_id: 菜谱 ID
        
        Returns:
            {'success': bool, 'instructions': List[Dict]}
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return {'success': False, 'error': '菜谱不存在'}
        
        instructions = []
        steps = recipe.get('steps', [])
        
        for i, step in enumerate(steps, 1):
            instructions.append({
                'step': i,
                'text': f"第{i}步：{step}",
                'duration_estimate': 30  # 预估每步朗读时间（秒）
            })
        
        return {
            'success': True,
            'recipe_title': recipe['title'],
            'instructions': instructions
        }


# 快速测试
if __name__ == '__main__':
    service = CookingService()
    
    logger.info("=== 做菜服务测试 ===\n")
    
    # 测试搜索菜谱
    logger.info("1. 搜索菜谱（西红柿炒蛋）...")
    result = service.search_recipes("西红柿炒蛋", limit=3)
    
    if result.get('success'):
        logger.info(f"   找到 {len(result.get('recipes', []))} 个菜谱\n")
        for i, recipe in enumerate(result.get('recipes', []), 1):
            logger.info(f"   [{i}] {recipe['title']}")
            logger.info(f"       作者：{recipe['author']}\n")
    else:
        logger.error(f"   搜索失败：{result.get('error')}\n")
    
    # 测试保存菜谱
    logger.info("2. 保存测试菜谱...")
    save_result = service.save_recipe(
        title="测试菜谱",
        ingredients=["鸡蛋 3 个", "西红柿 2 个", "盐 适量", "油 适量"],
        steps=["打散鸡蛋", "切西红柿", "炒鸡蛋", "加入西红柿翻炒", "调味出锅"],
        cook_time=10,
        difficulty="easy"
    )
    logger.info(f"   保存结果：{save_result}\n")
    
    # 测试获取已保存菜谱
    logger.info("3. 获取已保存菜谱...")
    recipes = service.get_saved_recipes()
    logger.info(f"   共 {len(recipes)} 个菜谱\n")
    
    # 测试创建计时器
    logger.info("4. 创建计时器...")
    timer_result = service.create_timer("煮鸡蛋", 300)  # 5 分钟
    logger.info(f"   创建结果：{timer_result}\n")
    
    # 测试添加食材
    logger.info("5. 添加食材到采购清单...")
    service.add_to_shopping_list("鸡蛋", "10", "个", "蛋类")
    service.add_to_shopping_list("西红柿", "5", "个", "蔬菜")
    logger.info("   添加完成\n")
    
    # 测试获取采购清单
    logger.info("6. 获取采购清单...")
    items = service.get_shopping_list()
    for item in items:
        logger.info(f"   - {item['item_name']} {item['quantity']}{item['unit']} ({item['category']})")
    
    logger.info("\n✅ 测试完成！")
