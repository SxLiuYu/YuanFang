#!/usr/bin/env python3
"""
贾维斯智能助理客户端工具

用法：
  jarvis -h                显示帮助信息
  jarvis hello             问候贾维斯
  jarvis whoami            你是谁？
  jarvis what is AI        AI 是什么？
  
  jarvis search "Python"   搜索相关信息
  jarvis weather           查询天气
  jarvis calendar          查看日历
  
  jarvis execute "ls -la"  执行命令
  jarvis speak "你好"       让贾维斯说话
  
  jarvis status            查看贾维斯状态
"""

import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json

# 贾维斯 API 地址
JARVIS_API = "http://localhost:8001"

# 初始化控制台
console = Console()

def print_banner():
    """打印贾维斯欢迎界面"""
    console.print(Panel([
        "╭──────────────────────────────────────────────╮",
        "│         🦞 JARVIS 智能助理系统 v1.0.0        │",
        "│         使命：让老于更好地生活                │",
        "╰──────────────────────────────────────────────╯",
    ]))

def print_welcome():
    """欢迎用户"""
    console.print("\n🎤 贾维斯已启动！您可以开始使用:")
    
def print_commands():
    """打印命令列表"""
    table = Table(show_header=True, header_style="bold cyan")
    
    commands = [
        ("🔹 问候与身份", "hello, whoami"),
        ("🔹 知识查询", "what is X, search X"),
        ("🔹 任务执行", "execute 'ls -la'"),
        ("🔹 语音交互", "speak '你好', listen"),
        ("🔹 系统状态", "status, health"),
    ]
    
    for category, examples in commands:
        table.add_row(category, ", ".join(examples))
    
    console.print(table)

def main():
    """主函数"""
    # 显示欢迎界面
    print_banner()
    
    if len(sys.argv) > 1:
        # 命令行模式
        command = sys.argv[1]
        
        if command in ["-h", "--help"]:
            print("\n📋 贾维斯命令列表:")
            print("""
  问候与身份:
    hello           - 问候贾维斯
    whoami          - 询问你是谁
    
  知识查询:
    what is X       - 解释概念
    search "topic"  - 搜索信息
    
  任务执行:
    execute "command" - 执行系统命令
    
  语音交互:
    speak "text"    - 让贾维斯说话
    listen           - 语音识别
    
  系统状态:
    status           - 查看贾维斯状态
    health           - 健康检查
    
示例:
  jarvis hello
  jarvis whoami  
  jarvis search "Python"
  jarvis execute "ls -la"
  jarvis speak "你好，老于！"
            """)
        elif command == "hello":
            print("\n👋 您好！我是贾维斯，您的智能助理。")
            print("我的使命是**让老于更好地生活**。")
        elif command == "whoami":
            print("\n🤖 我是贾维斯 (Jarvis)，由老于开发的智能助理。")
            print("核心框架：FastAPI + FinnA AI 模型 + CosyVoice2 语音")
            print("使命：让老于更好地生活")
        elif command == "status":
            try:
                response = subprocess.check_output(
                    f"curl -s {JARVIS_API}/api/status", 
                    shell=True, text=True
                )
                data = json.loads(response)
                print("\n📊 贾维斯状态:")
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    - {k}: {v}")
                    else:
                        print(f"  {key}: {'✓' if value else '✗'}")
            except Exception as e:
                print(f"\n⚠️ 无法获取状态：{e}")
        elif command == "health":
            try:
                response = subprocess.check_output(
                    f"curl -s {JARVIS_API}/health", 
                    shell=True, text=True
                )
                data = json.loads(response)
                print(f"\n✅ 贾维斯健康检查通过：{data['status']}")
            except Exception as e:
                print(f"\n⚠️ 无法进行健康检查：{e}")
        elif command.startswith("execute "):
            cmd = command.replace("execute ", "")
            print(f"\n📝 执行命令：{cmd}")
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if result.returncode == 0:
                    print("\n📄 输出:")
                    console.print(result.stdout)
                else:
                    print(f"\n❌ 命令执行失败:")
                    console.print(result.stderr)
            except Exception as e:
                print(f"\n❌ 执行错误：{e}")
        elif command.startswith("speak "):
            text = command.replace("speak ", "")
            print(f"\n🎤 贾维斯正在朗读：{text}")
        elif command.startswith("listen"):
            print("\n🎤 正在监听语音...")
        elif command.startswith("search "):
            query = command.replace("search ", "")
            print(f"\n🔍 正在搜索：{query}")
        elif command.startswith("what is "):
            topic = command.replace("what is ", "")
            print(f"\n📚 关于 {topic}...")
        else:
            print(f"\n💭 贾维斯正在思考您的问题：{command}")
    else:
        # 交互模式
        print_welcome()
        
        while True:
            try:
                user_input = input("\n贾维斯：").strip()
                
                if not user_input or user_input.lower() in ["quit", "exit"]:
                    print("\n再见！希望贾维斯能帮助您。")
                    break
                
                if user_input.startswith("execute "):
                    cmd = user_input.replace("execute ", "")
                    print(f"\n📝 执行命令：{cmd}")
                elif user_input.startswith("speak "):
                    text = user_input.replace("speak ", "")
                    print(f"\n🎤 贾维斯正在朗读：{text}")
                elif user_input.startswith("listen"):
                    print("\n🎤 正在监听语音...")
                else:
                    print(f"\n💭 贾维斯在思考您的问题...")
                    
            except KeyboardInterrupt:
                print("\n\n再见！")
                break

if __name__ == "__main__":
    main()
