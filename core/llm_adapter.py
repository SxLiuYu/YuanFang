"""
core/llm_adapter.py
FinnA API LiteLLM 封装 · LLMAdapter
支持 DeepSeek / Kimi / Qwen3-VL / CosyVoice2 / GLM-4.6 / Qwen3-32b
"""
import os
import json
import logging
import time
import urllib.request
import urllib.error
import ssl

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class LLMResponse:
    """LLM 响应封装"""
    def __init__(self, content: str, model: str = "", usage: dict = None, raw: dict = None):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.raw = raw or {}


class LLMAdapter:
    """
    FinnA / LiteLLM 统一适配器
    环境变量：
      FINNA_API_BASE    — API 地址（默认 https://www.finna.com.cn/v1）
      FINNA_API_KEY     — API Key
      OLLAMA_BASE       — Ollama 地址（默认 http://localhost:11434）
      LITELLM_BASE      — LiteLLM 地址
    """

    def __init__(self):
        self.api_base = os.getenv("FINNA_API_BASE", "https://www.finna.com.cn/v1").rstrip("/")
        self.api_key = os.getenv("FINNA_API_KEY", "")
        self.default_model = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"
        self.extra_backends = {}  # name -> base_url
        self._load_extra_backends()
        logger.info(f"[LLMAdapter] API base: {self.api_base}")

    def _load_extra_backends(self):
        """加载额外后端配置"""
        extra = os.getenv("LITELLM_EXTERNAL_BACKENDS", "")
        if not extra:
            return
        for pair in extra.split("|"):
            if "=" not in pair:
                continue
            name, url = pair.split("=", 1)
            self.extra_backends[name.strip()] = url.strip().rstrip("/")
        logger.info(f"[LLMAdapter] Extra backends: {self.extra_backends}")

    def _build_url(self, model: str) -> str:
        """根据模型名构建完整 URL"""
        if "/" in model:
            return f"{self.api_base}/{model}"
        return f"{self.api_base}/{model}"

    def _do_request(self, url: str, payload: dict, timeout: int = 60) -> dict:
        """发送 HTTP 请求到 LLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error(f"[LLMAdapter] HTTP {e.code}: {body[:200]}")
            raise RuntimeError(f"LLM API error {e.code}: {body[:200]}")
        except Exception as e:
            logger.error(f"[LLMAdapter] Request failed: {e}")
            raise

    # ──── 对话接口 ────

    def chat_simple(self, messages: list, model: str = None, temperature: float = 0.7,
                    json_mode: bool = False, max_tokens: int = 2048) -> str:
        """
        简单对话接口，返回纯文本
        messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
        """
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = self._build_url(model)
        try:
            resp = self._do_request(url, payload)
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"[LLMAdapter] Invalid response format: {e}, response: {resp}")
            raise RuntimeError(f"LLM response parse error: {e}")

    def chat_with_functions(self, messages: list, functions: list = None,
                           model: str = None, temperature: float = 0.3) -> LLMResponse:
        """
        带函数调用的对话接口
        functions: [{"name": "...", "parameters": {...}}]
        """
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "tools": [{"type": "function", "function": f} for f in (functions or [])],
        }
        url = self._build_url(model)
        resp = self._do_request(url, payload)
        try:
            choice = resp["choices"][0]
            msg = choice["message"]
            return LLMResponse(
                content=msg.get("content", ""),
                model=model,
                usage=resp.get("usage", {}),
                raw=resp,
            )
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"LLM response parse error: {e}")

    def chat_stream(self, messages: list, model: str = None,
                    temperature: float = 0.7, callback=None):
        """流式对话，callback(content片段) 会被调用"""
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        url = self._build_url(model)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                for line in resp:
                    line = line.decode("utf-8", errors="replace").strip()
                    if not line or line.startswith("data: "):
                        continue
                    if line.startswith("data: "):
                        line = line[7:]
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta and callback:
                            callback(delta)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            logger.error(f"[LLMAdapter] Stream error: {e}")
            raise

    def embed(self, text: str, model: str = "text-embedding-ada-002") -> list:
        """获取文本 embedding"""
        # FinnA 的 embedding 接口
        url = f"{self.api_base}/embeddings"
        payload = {"model": model, "input": text}
        resp = self._do_request(url, payload, timeout=30)
        try:
            return resp["data"][0]["embedding"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Embedding parse error: {e}")

    def models(self) -> list:
        """列出可用模型"""
        return [
            "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
            "Pro/kimi-lo혼/moonshot-v1-8k",
            "Pro/qwen/Qwen3-VL-32B-Instruct",
            "Pro/cosyvoice/cosyvoice2-1",
            "Pro/zai/glm-4.6",
            "Pro/zai/Qwen3-32b",
        ]


_llm: LLMAdapter | None = None


def get_llm() -> LLMAdapter:
    global _llm
    if _llm is None:
        _llm = LLMAdapter()
    return _llm
