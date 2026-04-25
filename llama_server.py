"""
llama.cpp-omni server 集成模块
MiniCPM-o 4.5 全双工 S2S（语音 → LLM → 语音）
用法:
  启动 server: python llama_server.py
  或在 Flask 里: from llama_server import LlamaServer
"""
import subprocess
import requests
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

LLAMA_SERVER = "/Users/sxliuyu/llama.cpp-omni/build/bin/llama-server"
MODEL_DIR = "/Users/sxliuyu/llama-models/MiniCPM-o-4_5-gguf"
PORT = 8090

class MiniCPMOmniServer:
    """MiniCPM-o 4.5 llama-omni server 封装"""
    
    def __init__(self, model_dir=MODEL_DIR, port=PORT):
        self.model_dir = model_dir
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"
    
    def start(self):
        """启动 llama-omni server"""
        model_path = os.path.join(self.model_dir, "MiniCPM-o-4_5-Q4_K_M.gguf")
        
        cmd = [
            LLAMA_SERVER,
            "-m", model_path,
            "--port", str(self.port),
            "--host", "0.0.0.0",
            "-ngl", "99",         # 99 GPU layers (Metal)
            "-c", "4096",         # 4K context
            "--no-tts",           # 文字模式（后续再加 TTS）
        ]
        
        logger.info(f"[LlamaServer] 启动: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        
        # 等待启动
        for i in range(30):
            try:
                r = requests.get(f"{self.base_url}/health", timeout=2)
                if r.status_code == 200:
                    logger.info(f"[LlamaServer] ✅ 就绪 (端口 {self.port})")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.error("[LlamaServer] 启动超时")
        return False
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("[LlamaServer] 已停止")
    
    def chat(self, message: str, system_prompt: str = None) -> str:
        """文字对话"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": "minicpm-o",
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 256, "temperature": 0.7}
        }
        
        try:
            r = requests.post(f"{self.base_url}/v1/chat/completions",
                            json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[LlamaServer] chat 错误: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    server = MiniCPMOmniServer()
    if server.start():
        print("Server 已启动，输入 exit 退出")
        while True:
            msg = input("> ")
            if msg.lower() == "exit":
                break
            resp = server.chat(msg)
            print(f"助手: {resp}")
        server.stop()
