"""
🦞 贾维�?- 核心能力引擎
整合龙虾军团所有能�?
"""
import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FINNA_API_BASE = os.getenv("FINNA_API_BASE", "https://www.finna.com.cn/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "app-6OzRGg93TfuDOny9NUnKMvQU")
QWEN_MODEL = "qwen3-32b"

# ============ 文件操作 ============
def move_files(pattern: str, dest: str) -> str:
    """移动匹配的文件到目标目录"""
    import glob
    source_dir = os.path.dirname(pattern) or "."
    files = glob.glob(pattern)
    if not files:
        return f"没有找到匹配 {pattern} 的文�?
    
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    moved = []
    for f in files:
        fname = os.path.basename(f)
        target = dest_path / fname
        shutil.move(f, target)
        moved.append(fname)
    
    return f"已移�?{len(moved)} 个文件到 {dest}: {', '.join(moved)}"

def find_files(keyword: str, path: str = ".") -> str:
    """搜索文件"""
    import glob
    results = []
    for f in Path(path).rglob("*"):
        if keyword.lower() in f.name.lower() and f.is_file():
            results.append(str(f))
    if not results:
        return f"没有找到包含 '{keyword}' 的文�?
    return "找到以下文件:\n" + "\n".join(results[:20])

def organize_downloads() -> str:
    """整理下载文件�?""
    downloads = str(Path.home() / "Downloads")
    patterns = {
        "Images": ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp"],
        "Documents": ["*.pdf", "*.doc", "*.docx", "*.txt", "*.xlsx", "*.pptx"],
        "Archives": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz"],
        "Audio": ["*.mp3", "*.wav", "*.flac", "*.m4a"],
        "Videos": ["*.mp4", "*.mkv", "*.avi", "*.mov"],
        "Code": ["*.py", "*.js", "*.html", "*.css", "*.json"],
    }
    
    results = []
    for folder, exts in patterns.items():
        for ext in exts:
            files = Path(downloads).glob(ext)
            for f in files:
                target = Path(downloads) / folder
                target.mkdir(exist_ok=True)
                fname = f.name
                counter = 1
                while (target / fname).exists():
                    fname = f.stem + f"_{counter}" + f.suffix
                    counter += 1
                shutil.move(str(f), target / fname)
                results.append(f"📦 {f.name} �?{folder}/")
    
    if not results:
        return "下载文件夹已经很整洁了，没有需要整理的文件"
    return "整理完成:\n" + "\n".join(results)

# ============ 日程与提�?============
def set_reminder(minutes: int, message: str) -> str:
    """设置提醒"""
    import sched, threading
    
    def remind():
        print(f"🔔 提醒: {message}")
        # 保存提醒到文件，供外部检�?
        with open("pending_reminder.txt", "w", encoding="utf-8") as f:
            f.write(message)
    
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(minutes * 60, 1, remind)
    thread = threading.Thread(target=scheduler.run)
    thread.start()
    
    return f"�?已设�?{minutes} 分钟后提�? {message}"

def check_reminder() -> str:
    """检查是否有待处理的提醒"""
    if os.path.exists("pending_reminder.txt"):
        with open("pending_reminder.txt", "r", encoding="utf-8") as f:
            msg = f.read().strip()
        if msg:
            os.remove("pending_reminder.txt")
            return msg
    return ""

# ============ 研究能力（调用多Agent�?============
def research_task(task: str) -> str:
    """使用多Agent进行研究"""
    from agents import LobsterArmyCrew
    crew = LobsterArmyCrew()
    result = crew.run(task)
    return result.get("final_response", str(result))

# ============ 天气 ============
def get_weather() -> str:
    """获取天气"""
    try:
        url = "https://wttr.in/?format=3&lang=zh"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except:
        return "获取天气失败"

# ============ 系统状�?============
def system_status() -> str:
    """获取系统状�?""
    import psutil
    
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    # 检查服务状�?
    services = {}
    for name, port in [("Flask API", 8000), ("Qdrant", 6333)]:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=2)
            services[name] = "�?
        except:
            services[name] = "�?
    
    return f"""系统状�?
- CPU: {cpu}%
- 内存: {mem}%
- 磁盘: {disk}%
- Flask API: {services.get('Flask API', '�?)}
- Qdrant: {services.get('Qdrant', '�?)}"""

# ============ 在家检�?============
def check_presence() -> str:
    """检查是否在�?""
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/presence",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            status = "在家 🏠" if data.get("is_home") else "不在�?🚶"
            return f"状�? {status}"
    except Exception as e:
        return f"检测失�? {str(e)}"

# ============ AI 对话 ============
def chat(text: str) -> str:
    """AI对话"""
    import urllib.request
    
    url = f"{FINNA_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "你是贾维斯，智能助手，用中文回答，简洁有力�?},
        {"role": "user", "content": text}
    ]
    data = {
        "model": QWEN_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0.7
    }
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"),
        headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"抱歉出错: {str(e)}"

# ============ 命令路由 ============
COMMANDS = {
    "move": move_files,
    "find": find_files,
    "organize": organize_downloads,
    "reminder": set_reminder,
    "weather": get_weather,
    "status": system_status,
    "presence": check_presence,
    "research": research_task,
    "chat": chat,
}

def parse_and_execute(text: str) -> str:
    """解析文本命令并执�?""
    text = text.strip()
    
    # 检查提�?
    reminder = check_reminder()
    if reminder:
        return f"🔔 提醒: {reminder}"
    
    # 关键词匹�?
    if any(k in text for k in ["移动", "move", "移到"]):
        # 简单解�? "移动 *.jpg �?Images"
        parts = text.replace("移动", "").split("�?)
        if len(parts) == 2:
            return move_files(parts[0].strip(), parts[1].strip())
    
    if any(k in text for k in ["搜索", "find", "�?]):
        import re
        match = re.search(r'[在]?(.+?)[里中]�?.+)', text)
        if match:
            return find_files(match.group(2).strip(), match.group(1).strip())
    
    if "整理下载" in text:
        return organize_downloads()
    
    if "提醒" in text:
        import re
        match = re.search(r'(\d+)\s*分钟', text)
        if match:
            mins = int(match.group(1))
            msg = text.replace(f"{mins}分钟后提�?, "").replace("提醒", "").strip()
            return set_reminder(mins, msg or "时间到了�?)
    
    if any(k in text for k in ["天气", "weather"]):
        return get_weather()
    
    if any(k in text for k in ["系统状�?, "status"]):
        return system_status()
    
    if any(k in text for k in ["在家", "presence"]):
        return check_presence()
    
    if any(k in text for k in ["研究", "调研", "research"]):
        return research_task(text)
    
    # 默认走AI对话
    return chat(text)

