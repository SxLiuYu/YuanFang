#!/usr/bin/env python3
"""
做菜功能测试脚本
"""

import requests
import json
import time

BASE_URL = 'http://localhost:8082'

def test_search_recipes():
    """测试菜谱搜索"""
    print("=== 测试菜谱搜索 ===\n")
    
    response = requests.get(f'{BASE_URL}/api/cooking/search', params={
        'keyword': '西红柿炒蛋',
        'limit': 3
    })
    
    result = response.json()
    print(f"状态：{'成功' if result.get('success') else '失败'}")
    print(f"找到 {result.get('count', 0)} 个菜谱\n")
    
    if result.get('success') and result.get('recipes'):
        for i, recipe in enumerate(result['recipes'], 1):
            print(f"[{i}] {recipe['title']}")
            print(f"    作者：{recipe['author']}")
            print(f"    链接：{recipe['url']}\n")

def test_save_recipe():
    """测试保存菜谱"""
    print("=== 测试保存菜谱 ===\n")
    
    recipe_data = {
        'title': '西红柿炒蛋',
        'ingredients': [
            '鸡蛋 3 个',
            '西红柿 2 个',
            '盐 适量',
            '油 适量',
            '葱花 少许'
        ],
        'steps': [
            '鸡蛋打散，加少许盐搅拌均匀',
            '西红柿洗净切块',
            '热锅凉油，倒入蛋液炒至凝固',
            '加入西红柿块翻炒出汁',
            '加盐调味，撒上葱花出锅'
        ],
        'cook_time': 10,
        'difficulty': 'easy',
        'source': '家庭秘方'
    }
    
    response = requests.post(
        f'{BASE_URL}/api/cooking/recipe/save',
        json=recipe_data
    )
    
    result = response.json()
    print(f"保存结果：{result}")
    
    if result.get('success'):
        print(f"菜谱 ID: {result['recipe_id']}\n")
        return result['recipe_id']
    
    return None

def test_get_recipes():
    """测试获取已保存菜谱"""
    print("=== 测试获取已保存菜谱 ===\n")
    
    response = requests.get(f'{BASE_URL}/api/cooking/recipes', params={
        'limit': 5
    })
    
    result = response.json()
    recipes = result.get('recipes', [])
    print(f"共 {len(recipes)} 个已保存菜谱\n")
    
    for i, recipe in enumerate(recipes, 1):
        print(f"[{i}] {recipe['title']}")
        print(f"    难度：{recipe['difficulty']}")
        print(f"    时间：{recipe['cook_time']}分钟\n")

def test_get_recipe_detail(recipe_id):
    """测试获取菜谱详情"""
    print(f"=== 测试获取菜谱详情 ({recipe_id}) ===\n")
    
    response = requests.get(f'{BASE_URL}/api/cooking/recipe/{recipe_id}')
    result = response.json()
    
    if result.get('success'):
        recipe = result['recipe']
        print(f"菜名：{recipe['title']}")
        print(f"难度：{recipe['difficulty']}")
        print(f"时间：{recipe['cook_time']}分钟\n")
        
        print("食材：")
        for ing in recipe.get('ingredients', []):
            print(f"  - {ing}")
        
        print("\n步骤：")
        for i, step in enumerate(recipe.get('steps', []), 1):
            print(f"  {i}. {step}")
        print()

def test_voice_instructions(recipe_id):
    """测试语音指导"""
    print(f"=== 测试语音指导 ===\n")
    
    response = requests.get(f'{BASE_URL}/api/cooking/recipe/{recipe_id}/voice')
    result = response.json()
    
    if result.get('success'):
        print(f"菜谱：{result['recipe_title']}\n")
        for inst in result.get('instructions', []):
            print(f"步骤{inst['step']}: {inst['text']}")
            print(f"  预计朗读时间：{inst['duration_estimate']}秒\n")

def test_timer():
    """测试计时器"""
    print("=== 测试计时器 ===\n")
    
    # 创建计时器
    print("1. 创建计时器（煮鸡蛋，5 分钟）...")
    response = requests.post(f'{BASE_URL}/api/cooking/timer', json={
        'timer_name': '煮鸡蛋',
        'duration_seconds': 300
    })
    result = response.json()
    print(f"   创建结果：{result}\n")
    
    if result.get('success'):
        timer_id = result['timer_id']
        
        # 获取计时器列表
        print("2. 获取计时器列表...")
        response = requests.get(f'{BASE_URL}/api/cooking/timers')
        timers = response.json().get('timers', [])
        for timer in timers:
            print(f"   - {timer['timer_name']}: {timer['remaining_seconds']}秒 ({timer['status']})")
        print()
        
        # 停止计时器
        print(f"3. 停止计时器 ({timer_id})...")
        response = requests.post(f'{BASE_URL}/api/cooking/timer/{timer_id}/stop')
        print(f"   结果：{response.json()}\n")

def test_shopping_list():
    """测试采购清单"""
    print("=== 测试采购清单 ===\n")
    
    # 添加食材
    print("1. 添加食材...")
    ingredients = [
        {'item_name': '鸡蛋', 'quantity': '10', 'unit': '个', 'category': '蛋类'},
        {'item_name': '西红柿', 'quantity': '5', 'unit': '个', 'category': '蔬菜'},
        {'item_name': '食用油', 'quantity': '1', 'unit': '瓶', 'category': '调料'},
        {'item_name': '盐', 'quantity': '1', 'unit': '袋', 'category': '调料'}
    ]
    
    for ing in ingredients:
        response = requests.post(f'{BASE_URL}/api/cooking/shopping-list', json=ing)
        print(f"   添加 {ing['item_name']}: {response.json()}")
    print()
    
    # 获取清单
    print("2. 获取采购清单...")
    response = requests.get(f'{BASE_URL}/api/cooking/shopping-list')
    items = response.json().get('items', [])
    
    print(f"   共 {len(items)} 项:\n")
    for item in items:
        print(f"   - {item['item_name']} {item['quantity']}{item['unit']} ({item['category']})")
    print()
    
    # 标记已采购
    if items:
        item_id = items[0]['item_id']
        print(f"3. 标记 {items[0]['item_name']} 已采购...")
        response = requests.post(f'{BASE_URL}/api/cooking/shopping-list/{item_id}/purchase', json={'purchased': True})
        print(f"   结果：{response.json()}\n")
        
        # 清空已采购
        print("4. 清空已采购项...")
        response = requests.post(f'{BASE_URL}/api/cooking/shopping-list/clear')
        print(f"   结果：{response.json()}\n")

if __name__ == '__main__':
    try:
        # 1. 搜索菜谱
        test_search_recipes()
        
        # 2. 保存菜谱
        recipe_id = test_save_recipe()
        
        if recipe_id:
            # 3. 获取已保存菜谱
            test_get_recipes()
            
            # 4. 获取菜谱详情
            test_get_recipe_detail(recipe_id)
            
            # 5. 语音指导
            test_voice_instructions(recipe_id)
        
        # 6. 计时器测试
        test_timer()
        
        # 7. 采购清单测试
        test_shopping_list()
        
        print("\n✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到家庭助手 API（http://localhost:8082）")
        print("   请先启动服务：python3 family_services_api.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
