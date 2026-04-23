# 语音交互功能

做菜场景的语音指导和语音控制功能

## 功能特性

### 1. 🎤 TTS 语音播报
- 菜谱介绍语音生成
- 分步语音指导
- 计时器提醒语音
- 确认反馈语音

### 2. 🗣️ 语音指令识别
- 下一步/上一步切换
- 重复当前步骤
- 启动/停止计时器
- 查看购物清单
- 添加食材
- 退出做菜模式

### 3. 🔊 语音交互流程
- 创建做菜会话
- 语音控制步骤
- 进度跟踪
- 自动计时器联动

## 前置依赖

### 安装 edge-tts

```bash
pip install edge-tts
```

### 可选：安装 ffprobe（获取音频时长）

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## API 接口

### TTS 语音生成

```
POST /api/voice/tts
Content-Type: application/json

{
  "text": "第 1 步：鸡蛋打散，加少许盐",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%"
}
```

**响应**
```json
{
  "success": true,
  "audio_path": "/tmp/tts_output/tts_20260306083000.mp3",
  "duration": 3.5
}
```

**参数**
- `text` (必填): 要转换的文本
- `voice` (可选): 语音音色
  - `zh-CN-XiaoxiaoNeural` - 中文女声（默认）
  - `zh-CN-YunxiNeural` - 中文男声
- `rate` (可选): 语速（如：+20%, -10%）

### 语音指令识别

```
POST /api/voice/recognize
Content-Type: application/json

{
  "text": "计时 5 分钟"
}
```

**响应**
```json
{
  "recognized": true,
  "command": "start_timer",
  "params": {
    "duration": 300,
    "timer_name": "计时器"
  },
  "confidence": 0.9
}
```

**支持的指令**

| 指令类型 | 关键词 | 参数 |
|---------|--------|------|
| next_step | 下一步、继续、下一个 | - |
| prev_step | 上一步、返回、上一个 | - |
| repeat_step | 重复、再说一遍 | - |
| start_timer | 开始计时、计时 | duration, timer_name |
| stop_timer | 停止计时、取消 | - |
| show_list | 购物清单、采购清单 | - |
| add_item | 添加到清单 | item_name, quantity, unit |
| exit | 退出、结束 | - |

### 开始做菜会话

```
POST /api/voice/cooking/start
Content-Type: application/json

{
  "recipe_id": "recipe_20260306083000"
}
```

**响应**
```json
{
  "success": true,
  "session_id": "cooking_20260306083000",
  "recipe_title": "西红柿炒蛋",
  "total_steps": 5,
  "intro_audio": "/tmp/tts_output/tts_20260306083001.mp3"
}
```

### 获取下一步语音

```
POST /api/voice/cooking/{session_id}/next
```

**响应**
```json
{
  "success": true,
  "step": 1,
  "total": 5,
  "text": "第 1 步：鸡蛋打散，加少许盐搅拌均匀",
  "audio_path": "/tmp/tts_output/tts_20260306083002.mp3"
}
```

### 处理语音指令

```
POST /api/voice/cooking/{session_id}/command
Content-Type: application/json

{
  "text": "计时 3 分钟"
}
```

**响应**
```json
{
  "success": true,
  "action": "create_timer",
  "timer_name": "计时器",
  "duration": 180,
  "timer_id": 1,
  "audio_path": "/tmp/tts_output/tts_20260306083003.mp3"
}
```

### 获取会话状态

```
GET /api/voice/cooking/{session_id}/status
```

**响应**
```json
{
  "session_id": "cooking_20260306083000",
  "recipe_title": "西红柿炒蛋",
  "current_step": 2,
  "total_steps": 5,
  "progress": 0.4
}
```

### 结束会话

```
POST /api/voice/cooking/{session_id}/end
```

### 计时器提醒语音

```
POST /api/voice/timer-alert
Content-Type: application/json

{
  "timer_name": "煮鸡蛋"
}
```

**响应**
```json
{
  "success": true,
  "audio_path": "/tmp/tts_output/tts_20260306083004.mp3"
}
```

## 使用示例

### Python 客户端

```python
import requests
import time

BASE_URL = 'http://localhost:8082'

# 1. 创建菜谱
response = requests.post(f'{BASE_URL}/api/cooking/recipe/save', json={
    'title': '西红柿炒蛋',
    'ingredients': ['鸡蛋 3 个', '西红柿 2 个', '盐 适量'],
    'steps': [
        '鸡蛋打散，加少许盐',
        '西红柿洗净切块',
        '热锅凉油，倒入蛋液',
        '加入西红柿翻炒',
        '调味出锅'
    ],
    'cook_time': 10,
    'difficulty': 'easy'
})
recipe_id = response.json()['recipe_id']

# 2. 开始做菜会话
response = requests.post(f'{BASE_URL}/api/voice/cooking/start', json={
    'recipe_id': recipe_id
})
session_id = response.json()['session_id']
intro_audio = response.json()['intro_audio']

# 播放介绍语音
play_audio(intro_audio)

# 3. 语音指导流程
while True:
    # 获取下一步
    response = requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/next')
    result = response.json()
    
    if not result['success']:
        print("已经是最后一步了")
        break
    
    print(f"步骤 {result['step']}/{result['total']}: {result['text']}")
    
    # 播放语音
    play_audio(result['audio_path'])
    
    # 等待用户指令
    user_input = input("下一步/上一步/计时/退出：")
    
    # 处理语音指令
    response = requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/command', json={
        'text': user_input
    })
    cmd_result = response.json()
    
    if cmd_result.get('action') == 'create_timer':
        print(f"创建计时器：{cmd_result['timer_name']} {cmd_result['duration']}秒")
    
    if '退出' in user_input:
        break

# 4. 结束会话
requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/end')
```

### 集成语音识别（前端）

```javascript
// 使用 Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.lang = 'zh-CN';
recognition.continuous = false;

recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    
    // 发送到后端识别
    const response = await fetch('/api/voice/recognize', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: transcript})
    });
    
    const result = await response.json();
    
    if (result.recognized) {
        // 处理指令
        handleCommand(result.command, result.params);
    }
};

recognition.start();
```

### 播放音频

```python
# Python 播放音频
import pygame
import time

def play_audio(audio_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    pygame.mixer.quit()
```

## 完整做菜流程

```
1. 用户："帮我做西红柿炒蛋"
   → 搜索菜谱 → 创建会话 → 播放介绍

2. 系统："第 1 步：鸡蛋打散，加少许盐"
   → 播放语音 → 等待指令

3. 用户："下一步"
   → 识别指令 → 播放下一步语音

4. 用户："计时 3 分钟"
   → 创建计时器 → 播放确认语音

5. 计时器响
   → 播放提醒语音 → 继续下一步

6. 用户："退出"
   → 结束会话
```

## 测试

```bash
# 启动服务
cd /home/admin/.openclaw/workspace/openclaw-clients/backend/services
python3 family_services_api.py

# 运行测试
python3 test_voice.py
```

## 语音音色选择

edge-tts 支持的中文音色：

- **zh-CN-XiaoxiaoNeural** - 女声（温暖、亲切）- 默认
- **zh-CN-YunxiNeural** - 男声（沉稳、专业）
- **zh-CN-XiaoyiNeural** - 女声（活泼）
- **zh-CN-YunjianNeural** - 男声（运动、激情）

更多音色查看：https://github.com/rany2/edge-tts

## 文件列表

- `voice_interaction_service.py` - 语音交互核心服务
- `family_services_api.py` - API 接口（已集成）
- `test_voice.py` - 测试脚本
- `VOICE_INTERACTION.md` - 本文档

## 下一步优化

1. ⏳ **实时语音识别** - 集成 Whisper/讯飞
2. ⏳ **多轮对话** - 上下文理解
3. ⏳ **情感语音** - 根据场景调整语调
4. ⏳ **离线 TTS** - 支持离线场景
5. ⏳ **语音唤醒** - "小助手，开始做菜"
