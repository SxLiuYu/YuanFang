"""
Recipe Recommendation — 根据现有食材推荐菜谱
存储常用菜谱，或者根据现有食材推荐做法
"""

import json
import os
import random
from typing import Dict, List, Optional

# 数据文件
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RECIPE_FILE = os.path.join(DATA_DIR, "recipes.json")

# 内置基础菜谱库
DEFAULT_RECIPES = [
    {
        "name": "番茄炒蛋",
        "ingredients": ["番茄", "鸡蛋", "盐", "糖", "油"],
        "steps": [
            "番茄切块，鸡蛋打散加少许盐",
            "热油煎炒鸡蛋，盛出备用",
            "热油炒番茄出汁，加糖盐调味",
            "倒入鸡蛋一起翻炒均匀出锅"
        ],
        "difficulty": "简单",
        "time": "10分钟"
    },
    {
        "name": "鸡蛋炒饭",
        "ingredients": ["米饭", "鸡蛋", "葱花", "盐", "油"],
        "steps": [
            "米饭最好隔夜，打散",
            "鸡蛋打散煎熟盛出",
            "热油炒米饭，压散",
            "加入鸡蛋翻炒，加盐调味，撒葱花出锅"
        ],
        "difficulty": "简单",
        "time": "10分钟"
    },
    {
        "name": "酸辣土豆丝",
        "ingredients": ["土豆", "醋", "辣椒", "盐", "蒜", "油"],
        "steps": [
            "土豆切丝泡水去淀粉",
            "热油爆香蒜和辣椒",
            "大火翻炒土豆丝，加醋加盐",
            "翻炒几分钟出锅，保持脆感"
        ],
        "difficulty": "简单",
        "time": "15分钟"
    },
    {
        "name": "红烧排骨",
        "ingredients": ["排骨", "葱姜", "生抽", "老抽", "糖", "料酒"],
        "steps": [
            "排骨冷水下锅焯水捞出",
            "热油炒糖色，倒入排骨上色",
            "加葱姜料酒生抽老抽，加水没过",
            "大火烧开转小火炖40分钟，大火收汁"
        ],
        "difficulty": "中等",
        "time": "60分钟"
    },
    {
        "name": "拍黄瓜",
        "ingredients": ["黄瓜", "蒜", "醋", "生抽", "香油", "盐"],
        "steps": [
            "黄瓜洗净拍碎切段",
            "蒜切末",
            "加所有调料拌匀，放十分钟入味即可"
        ],
        "difficulty": "简单",
        "time": "5分钟"
    },
    {
        "name": "蒜蓉青菜",
        "ingredients": ["青菜", "蒜", "盐", "油"],
        "steps": [
            "蒜剁成蒜蓉",
            "热油爆香蒜蓉",
            "放入青菜快速翻炒，加盐调味",
            "青菜变软即可出锅"
        ],
        "difficulty": "简单",
        "time": "5分钟"
    }
]


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_recipes() -> dict:
    if not os.path.exists(RECIPE_FILE):
        # 初始化，加入默认菜谱
        data = {"recipes": DEFAULT_RECIPES.copy()}
        _save_recipes(data)
        return data
    
    try:
        with open(RECIPE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"recipes": DEFAULT_RECIPES.copy()}


def _save_recipes(data: dict) -> bool:
    _ensure_data_dir()
    try:
        with open(RECIPE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


def add_recipe(name: str, ingredients: List[str], steps: List[str], difficulty: str = "简单", time: str = None) -> str:
    """添加新菜谱"""
    data = _load_recipes()
    # 检查是否存在
    for r in data["recipes"]:
        if r["name"] == name:
            return f"{name} 菜谱已经存在"
    
    recipe = {
        "name": name,
        "ingredients": ingredients,
        "steps": steps,
        "difficulty": difficulty,
        "time": time or "未知"
    }
    data["recipes"].append(recipe)
    _save_recipes(data)
    return f"已添加菜谱：{name}"


def search_recipe_by_ingredient(ingredient: str) -> str:
    """根据食材搜索菜谱"""
    data = _load_recipes()
    matches = []
    
    for r in data["recipes"]:
        for ing in r["ingredients"]:
            if ingredient.lower() in ing.lower():
                matches.append(r)
                break
    
    if not matches:
        return f"找不到包含 {ingredient} 的菜谱，你可以添加新菜谱"
    
    lines = [f"找到 {len(matches)} 个包含 {ingredient} 的菜谱："]
    for i, r in enumerate(matches, 1):
        lines.append(f"{i}. **{r['name']}** ({r['difficulty']}, {r['time']})")
        lines.append(f"   食材：{', '.join(r['ingredients'])}")
    
    return "\n".join(lines)


def get_recipe(name: str) -> Optional[str]:
    """获取完整菜谱做法"""
    data = _load_recipes()
    
    for r in data["recipes"]:
        if r["name"] == name or name.lower() in r["name"].lower():
            lines = [f"🍳 {r['name']}"]
            lines.append(f"难度：{r['difficulty']}  预计时间：{r['time']}")
            lines.append(f"食材：{', '.join(r['ingredients'])}")
            lines.append("")
            lines.append("做法：")
            for j, step in enumerate(r["steps"], 1):
                lines.append(f"{j}. {step}")
            return "\n".join(lines)
    
    return None


def random_recipe() -> str:
    """随机推荐一个菜谱"""
    data = _load_recipes()
    if not data["recipes"]:
        return "还没有保存任何菜谱"
    
    recipe = random.choice(data["recipes"])
    lines = [f"🎲 今天推荐你做：{recipe['name']}"]
    lines.append(f"难度：{recipe['difficulty']}  预计时间：{recipe['time']}")
    lines.append(f"食材：{', '.join(recipe['ingredients'])}")
    lines.append("")
    lines.append("做法：")
    for j, step in enumerate(recipe["steps"], 1):
        lines.append(f"{j}. {step}")
    return "\n".join(lines)


def list_all_recipes() -> str:
    """列出所有菜谱"""
    data = _load_recipes()
    recipes = data["recipes"]
    
    if not recipes:
        return "还没有保存任何菜谱"
    
    lines = [f"已保存 {len(recipes)} 个菜谱："]
    for i, r in enumerate(recipes, 1):
        lines.append(f"{i}. {r['name']} ({r['difficulty']}, {r['time']})")
    
    return "\n".join(lines)


def recipe_handler(text: str) -> Optional[str]:
    """菜谱意图处理"""
    text = text.lower().strip()
    
    # 随机推荐
    if ("随便" in text or "推荐一个" in text or "随机" in text) and ("菜" in text or "菜谱" in text):
        return random_recipe()
    
    # 列出所有
    if ("列出" in text or "看一下" in text) and ("菜谱" in text or "所有菜" in text):
        return list_all_recipes()
    
    # 添加菜谱
    if ("添加" in text or "记下来" in text) and ("菜谱" in text or "做法" in text):
        # 这个太复杂，让LLM处理吧，这里只做简单匹配
        # "我想要菜谱鸡蛋番茄" -> 搜索
        pass
    
    # 根据食材搜索
    # "有土豆能做什么菜" / "推荐一个鸡蛋的菜谱"
    ingredients = [
        "土豆", "番茄", "鸡蛋", "排骨", "牛肉", "鸡肉", "鱼", 
        "青菜", "黄瓜", "茄子", "豆腐", "米饭", "猪肉"
    ]
    for ing in ingredients:
        if ing in text and ("做什么" in text or "能做" in text or "菜谱" in text):
            return search_recipe_by_ingredient(ing)
    
    # 查询具体菜谱
    data = _load_recipes()
    for r in data["recipes"]:
        if r["name"].lower() in text:
            result = get_recipe(r["name"])
            if result:
                return result
    
    # "怎么做番茄炒蛋"
    if ("怎么做" in text or "做法" in text):
        name = text.replace("怎么做", "").replace("做法", "").replace("给我", "").strip()
        if name:
            result = get_recipe(name)
            if result:
                return result
    
    return None