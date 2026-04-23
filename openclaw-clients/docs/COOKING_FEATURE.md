# 做菜功能

家庭助手做菜功能 - 语音指导、计时器、食材采购清单

## 功能概览

### 1. 📖 菜谱管理
- 搜索小红书菜谱
- 保存常用菜谱到本地
- 获取菜谱详情

### 2. 🎤 语音指导
- 分步语音播报
- 步骤文本转语音（TTS）

### 3. ⏱️ 计时器
- 多步骤计时
- 倒计时提醒
- 关联菜谱步骤

### 4. 🛒 食材采购清单
- 自动生成购物清单
- 分类管理（蔬菜/肉类/调料）
- 标记已采购

## API 接口

### 菜谱搜索

```
GET /api/cooking/search?keyword=西红柿炒蛋&limit=5
```

**响应**
```json
{
  "success": true,
  "keyword": "西红柿炒蛋",
  "count": 5,
  "recipes": [
    {
      "recipe_id": "693e5aa3000000001e00d307",
      "title": "超简单的西红柿炒蛋",
      "author": "美食达人",
      "cover_image": "http://...",
      "url": "https://www.xiaohongshu.com/explore/..."
    }
  ]
}
```

### 保存菜谱

```
POST /api/cooking/recipe/save
Content-Type: application/json

{
  "title": "西红柿炒蛋",
  "ingredients": ["鸡蛋 3 个", "西红柿 2 个", "盐 适量", "油 适量"],
  "steps": ["打散鸡蛋", "切西红柿", "炒鸡蛋", "加入西红柿翻炒", "调味出锅"],
  "cook_time": 10,
  "difficulty": "easy"
}
```

**响应**
```json
{"success": true, "recipe_id": "recipe_20260306081500"}
```

### 获取已保存菜谱

```
GET /api/cooking/recipes?limit=20
```

### 获取单个菜谱

```
GET /api/cooking/recipe/{recipe_id}
```

### 获取语音指导

```
GET /api/cooking/recipe/{recipe_id}/voice
```

**响应**
```json
{
  "success": true,
  "recipe_title": "西红柿炒蛋",
  "instructions": [
    {
      "step": 1,
      "text": "第 1 步：打散鸡蛋",
      "duration_estimate": 30
    },
    {
      "step": 2,
      "text": "第 2 步：切西红柿",
      "duration_estimate": 30
    }
  ]
}
```

### 创建计时器

```
POST /api/cooking/timer
Content-Type: application/json

{
  "timer_name": "煮鸡蛋",
  "duration_seconds": 300,
  "recipe_id": "recipe_20260306081500",
  "step_number": 1
}
```

**响应**
```json
{"success": true, "timer_id": 1}
```

### 获取计时器列表

```
GET /api/cooking/timers?status=running
```

**响应**
```json
{
  "timers": [
    {
      "timer_id": 1,
      "timer_name": "煮鸡蛋",
      "duration_seconds": 300,
      "remaining_seconds": 240,
      "status": "running",
      "step_number": 1
    }
  ]
}
```

### 停止计时器

```
POST /api/cooking/timer/{timer_id}/stop
```

### 完成计时器

```
POST /api/cooking/timer/{timer_id}/complete
```

### 添加食材到采购清单

```
POST /api/cooking/shopping-list
Content-Type: application/json

{
  "item_name": "鸡蛋",
  "quantity": "10",
  "unit": "个",
  "category": "蛋类",
  "note": "买新鲜的"
}
```

### 将菜谱食材添加到采购清单

```
POST /api/cooking/recipe/{recipe_id}/ingredients
```

### 获取采购清单

```
GET /api/cooking/shopping-list?purchased=false
```

**响应**
```json
{
  "items": [
    {
      "item_id": 1,
      "item_name": "鸡蛋",
      "quantity": "10",
      "unit": "个",
      "category": "蛋类",
      "purchased": false
    },
    {
      "item_id": 2,
      "item_name": "西红柿",
      "quantity": "5",
      "unit": "个",
      "category": "蔬菜",
      "purchased": false
    }
  ]
}
```

### 标记已采购

```
POST /api/cooking/shopping-list/{item_id}/purchase
Content-Type: application/json

{"purchased": true}
```

### 删除采购项

```
DELETE /api/cooking/shopping-list/{item_id}
```

### 清空已采购项

```
POST /api/cooking/shopping-list/clear
```

## 使用示例

### Python 客户端

```python
import requests

BASE_URL = 'http://localhost:8082'

# 1. 搜索菜谱
response = requests.get(f'{BASE_URL}/api/cooking/search', params={
    'keyword': '西红柿炒蛋',
    'limit': 3
})
recipes = response.json()['recipes']
print(f"找到 {len(recipes)} 个菜谱")

# 2. 保存菜谱
response = requests.post(f'{BASE_URL}/api/cooking/recipe/save', json={
    'title': '西红柿炒蛋',
    'ingredients': ['鸡蛋 3 个', '西红柿 2 个', '盐 适量'],
    'steps': ['打散鸡蛋', '切西红柿', '炒鸡蛋', '混合翻炒', '调味出锅'],
    'cook_time': 10,
    'difficulty': 'easy'
})
recipe_id = response.json()['recipe_id']
print(f"保存成功：{recipe_id}")

# 3. 获取语音指导
response = requests.get(f'{BASE_URL}/api/cooking/recipe/{recipe_id}/voice')
instructions = response.json()['instructions']
for step in instructions:
    print(f"{step['text']} (约{step['duration_estimate']}秒)")

# 4. 创建计时器
response = requests.post(f'{BASE_URL}/api/cooking/timer', json={
    'timer_name': '炒鸡蛋',
    'duration_seconds': 180,  # 3 分钟
    'step_number': 3
})
timer_id = response.json()['timer_id']
print(f"计时器已启动：{timer_id}")

# 5. 添加食材到采购清单
response = requests.post(f'{BASE_URL}/api/cooking/shopping-list', json={
    'item_name': '鸡蛋',
    'quantity': '10',
    'unit': '个',
    'category': '蛋类'
})

# 6. 获取采购清单
response = requests.get(f'{BASE_URL}/api/cooking/shopping-list')
items = response.json()['items']
print("\n采购清单：")
for item in items:
    print(f"  - {item['item_name']} {item['quantity']}{item['unit']}")
```

### 语音指令示例

```
"帮我找个西红柿炒蛋的做法"
"开始做菜模式，第一步计时 5 分钟"
"把鸡蛋和西红柿加到购物清单"
"显示我的采购清单"
"语音播报做菜步骤"
```

## 测试

```bash
# 启动服务
cd /home/admin/.openclaw/workspace/openclaw-clients/backend/services
python3 family_services_api.py

# 运行测试
python3 cooking_service.py
```

## 数据库表结构

### recipes (菜谱表)
- recipe_id: 唯一 ID
- title: 菜名
- source: 来源
- author: 作者
- ingredients: 食材列表（JSON）
- steps: 步骤列表（JSON）
- cook_time: 烹饪时间
- difficulty: 难度
- cover_image: 封面图
- favorited: 是否收藏

### timers (计时器表)
- timer_name: 计时器名称
- duration_seconds: 总时长
- remaining_seconds: 剩余时间
- status: 状态（running/stopped/completed）
- recipe_id: 关联菜谱
- step_number: 关联步骤

### shopping_list (采购清单)
- item_name: 食材名称
- quantity: 数量
- unit: 单位
- category: 分类
- recipe_id: 关联菜谱
- purchased: 是否已采购

## 集成 TTS 语音播报

结合 OpenClaw TTS 功能：

```python
# 获取语音指导文本
response = requests.get(f'{BASE_URL}/api/cooking/recipe/{recipe_id}/voice')
instructions = response.json()['instructions']

# 逐条播报
for step in instructions:
    text = step['text']
    # 调用 TTS
    tts_response = requests.post('http://localhost:8080/tts', json={'text': text})
    # 播放音频
    play_audio(tts_response.json()['audio_path'])
```

## 文件列表

- `cooking_service.py` - 做菜服务核心逻辑
- `family_services_api.py` - API 接口（已集成）
- `test_cooking.py` - 测试脚本（待创建）
- `COOKING_FEATURE.md` - 本文档

## 下一步优化

1. ⏳ **智能食材识别** - 从菜谱自动提取食材清单
2. ⏳ **营养分析** - 计算热量、营养成分
3. ⏳ **菜谱推荐** - 根据现有食材推荐菜谱
4. ⏳ **语音交互** - 语音控制计时器、切换步骤
5. ⏳ **分享功能** - 分享菜谱到家庭群
