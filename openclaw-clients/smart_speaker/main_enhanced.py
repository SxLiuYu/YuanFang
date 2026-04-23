#!/usr/bin/env python3
"""
OpenClaw 智能音箱 - 增强版
支持 TTS、多轮对话、历史记录
"""

import os
import sys
import json
import time
import speech_recognition as sr
from datetime import datetime
from pathlib import Path

# 尝试导入 TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("警告：pyttsx3 未安装，TTS 功能不可用。运行：pip install pyttsx3")

# 尝试导入 HTTP 请求
try:
    import requests
except ImportError:
    print("错误：requests 未安装。运行：pip install requests")
    sys.exit(1)

class ConversationManager:
    """对话管理器 - 多轮对话和历史记录"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.context_file = self.data_dir / "context.json"
        self.history_file = self.data_dir / "history.json"
        self.max_context_size = 20
        self.max_history_count = 50
        
        self.context = []
        self.history = []
        self.load()
    
    def load(self):
        """加载数据"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
            except:
                self.context = []
        
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def save(self):
        """保存数据"""
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_to_context(self, role: str, content: str):
        """添加到上下文"""
        self.context.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制大小
        if len(self.context) > self.max_context_size:
            self.context = self.context[-self.max_context_size:]
        
        self.save()
    
    def get_context_for_api(self, max_messages: int = 10):
        """获取 API 用的上下文"""
        messages = [{
            "role": "system",
            "content": "你是一个智能音箱助手，请简洁回答。保持对话连贯性。"
        }]
        
        # 添加最近的上下文
        start = max(0, len(self.context) - max_messages)
        messages.extend(self.context[start:])
        
        return messages
    
    def add_to_history(self, messages: list):
        """添加到历史"""
        if not messages:
            return
        
        preview = next((m["content"] for m in messages if m["role"] == "user"), "对话")
        session = {
            "id": datetime.now().timestamp(),
            "preview": preview[:50],
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        self.history.insert(0, session)
        
        # 限制数量
        if len(self.history) > self.max_history_count:
            self.history = self.history[:self.max_history_count]
        
        self.save()
    
    def get_history(self):
        """获取历史"""
        return self.history
    
    def clear_context(self):
        """清空上下文"""
        self.context = []
        self.save()
    
    def clear_history(self):
        """清空历史"""
        self.history = []
        self.save()


class SmartSpeaker:
    """智能音箱主类"""
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            print("警告：未设置 DASHSCOPE_API_KEY 环境变量")
        
        self.conversation = ConversationManager()
        self.recognizer = sr.Recognizer()
        self.tts_engine = None
        
        if TTS_AVAILABLE:
            self.init_tts()
    
    def init_tts(self):
        """初始化 TTS"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 1.0)
            
            # 尝试设置中文语音
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'zh' in voice.languages or 'chinese' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"TTS 初始化失败：{e}")
            self.tts_engine = None
    
    def speak(self, text: str):
        """TTS 朗读"""
        if not self.tts_engine:
            print(f"AI: {text}")
            return
        
        try:
            print(f"AI: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS 朗读失败：{e}")
            print(text)
    
    def listen(self):
        """语音识别"""
        with sr.Microphone() as source:
            print("🎤 正在听... (说话或按 Ctrl+C 取消)")
            try:
                audio = self.recognizer.listen(source, timeout=5)
            except sr.WaitTimeoutError:
                print("⏱️ 超时，未检测到声音")
                return None
        
        try:
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            print(f"你：{text}")
            return text
        except sr.UnknownValueError:
            print("❌ 无法识别语音")
            return None
        except sr.RequestError as e:
            print(f"❌ 语音识别服务错误：{e}")
            return None
    
    def call_api(self, user_message: str):
        """调用 DashScope API"""
        if not self.api_key:
            return "API 密钥未配置，请设置 DASHSCOPE_API_KEY 环境变量"
        
        # 获取上下文
        messages = self.conversation.get_context_for_api(10)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-max",
                    "input": {"messages": messages},
                    "parameters": {
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["output"]["choices"][0]["message"]["content"]
                
                # 更新上下文
                self.conversation.add_to_context("user", user_message)
                self.conversation.add_to_context("assistant", content)
                
                return content
            else:
                return f"API 错误：{response.status_code}"
        
        except Exception as e:
            return f"请求失败：{e}"
    
    def show_history(self):
        """显示历史记录"""
        history = self.conversation.get_history()
        
        if not history:
            print("\n📜 暂无历史记录")
            return
        
        print("\n📜 历史记录:")
        for i, session in enumerate(history[:10], 1):
            date = datetime.fromisoformat(session["timestamp"]).strftime("%m-%d %H:%M")
            print(f"{i}. [{date}] {session['preview']}... ({len(session['messages'])}条消息)")
    
    def run_interactive(self):
        """交互模式"""
        print("\n" + "="*50)
        print("🤖 OpenClaw 智能音箱 - 增强版")
        print("="*50)
        print("命令:")
        print("  [说话] - 直接说话")
        print("  h      - 查看历史")
        print("  c      - 清空上下文")
        print("  q      - 退出")
        print("="*50 + "\n")
        
        while True:
            try:
                cmd = input("指令> ").strip().lower()
                
                if cmd == 'q':
                    print("👋 再见！")
                    break
                elif cmd == 'h':
                    self.show_history()
                elif cmd == 'c':
                    self.conversation.clear_context()
                    print("✅ 上下文已清空")
                elif cmd == '':
                    # 直接语音
                    text = self.listen()
                    if text:
                        response = self.call_api(text)
                        self.speak(response)
                else:
                    # 文本输入
                    response = self.call_api(cmd)
                    self.speak(response)
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误：{e}")
    
    def run_voice_only(self):
        """纯语音模式"""
        print("\n🤖 OpenClaw 智能音箱 - 语音模式")
        print("按 Ctrl+C 退出\n")
        
        while True:
            try:
                text = self.listen()
                if text:
                    response = self.call_api(text)
                    self.speak(response)
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误：{e}")
                time.sleep(1)


def main():
    import sys
    
    speaker = SmartSpeaker()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--voice':
        speaker.run_voice_only()
    else:
        speaker.run_interactive()


if __name__ == "__main__":
    main()
