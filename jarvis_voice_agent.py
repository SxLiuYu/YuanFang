#!/usr/bin/env python3
"""
Jarvis Voice Agent — 实时连续语音对话
麦克风 → VAD → Whisper STT → Qwen3.5-4B 流式推理 → Kokoro TTS → 实时播放

管线流程:
  [麦克风] → [silero-vad] → [whisper] → [Qwen3.5流式] → [Kokoro TTS] → [音频播放]
              ↑                                              ↓
              └──────────────────── 持续监听 ←───────────────┘

Usage:
    python3 jarvis_voice_agent.py [--唤醒词元芳]
"""

import os
import sys
import time
import queue
import threading
import warnings
import argparse
import logging
import subprocess
from pathlib import Path

# 尝试使用统一配置，如果在后端项目外则使用默认值
try:
    import sys
    sys.path.insert(0, '/Users/sxliuyu/YuanFang/core/config')
    from config import get_config
    config = get_config()
    jarvis_config = config.jarvis_voice
    OMLX_BASE_URL = jarvis_config.omlx_base_url
    OMLX_AUTH = jarvis_config.omlx_auth
    DEFAULT_MODEL = jarvis_config.default_model
    KOKORO_MODEL = jarvis_config.kokoro_model
    DEFAULT_VOICE = jarvis_config.default_voice
    OUTPUT_DIR = Path(jarvis_config.output_dir).expanduser()
    VAD_THRESHOLD = jarvis_config.vad_threshold
    VAD_MIN_SAMPLES = int(jarvis_config.vad_min_samples * jarvis_config.sample_rate)  # 采样数
    SAMPLE_RATE = jarvis_config.sample_rate
    CHUNK_SIZE = jarvis_config.chunk_size
    INTERRUPTION_THRESHOLD = jarvis_config.interruption_threshold
    MIN_INTERRUPTION_INTERVAL = jarvis_config.min_interruption_interval
except (ImportError, AttributeError):
    # 独立运行时使用默认配置
    warnings.filterwarnings("ignore")
    os.environ["HF_HUB_OFFLINE"] = "1"
    # ==================== 配置 ====================
    OMLX_BASE_URL = "http://localhost:4560"
    OMLX_AUTH = "*** jarvis-local"
    DEFAULT_MODEL = "Qwen3.5-4B-MLX-4bit"
    KOKORO_MODEL = "prince-canuma/Kokoro-82M"
    DEFAULT_VOICE = "af_heart"
    OUTPUT_DIR = Path("~/YuanFang/data/audio").expanduser()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # VAD 配置
    VAD_THRESHOLD = 0.5
    VAD_MIN_SAMPLES = int(16000 * 0.3)  # 至少 300ms 语音

    # 音频配置
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 5120  # 320ms per chunk

    # 打断配置
    INTERRUPTION_THRESHOLD = 0.15  # 能量阈值触发打断（相对背景）
    MIN_INTERRUPTION_INTERVAL = 0.5  # 两次打断最小间隔（秒）

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# 全局播放进程跟踪
_playing_processes = []
_playing_processes_lock = threading.Lock()

def track_playback_process(proc: subprocess.Popen):
    """跟踪播放进程"""
    with _playing_processes_lock:
        _playing_processes.append(proc)

def stop_all_playback():
    """停止所有正在播放的音频"""
    with _playing_processes_lock:
        stopped = 0
        for proc in _playing_processes:
            if proc.poll() is None:  # 进程还在运行
                try:
                    proc.terminate()
                    proc.wait(timeout=0.5)
                    stopped += 1
                except:
                    pass
        _playing_processes.clear()
        return stopped

# ==================== 依赖检查 ====================
def check_dependencies():
    """检查必要的库和模型"""
    deps = {}
    
    # OMLX Server
    try:
        import requests
        r = requests.get(f"{OMLX_BASE_URL}/health", timeout=5)
        deps["omlx"] = r.json().get("default_model", "unknown")
    except Exception as e:
        deps["omlx"] = f"❌ {e}"
    
    # mlx_whisper
    try:
        import mlx_whisper
        deps["whisper"] = "✅"
    except ImportError:
        deps["whisper"] = "❌ 需要 pip install mlx-whisper"
    
    # mlx_audio
    try:
        from mlx_audio.tts.generate import generate_audio
        deps["kokoro"] = "✅"
    except ImportError:
        deps["kokoro"] = "❌ 需要 pip install mlx-audio"
    
    # openwakeword (唤醒词)
    try:
        import openwakeword
        deps["wakeword"] = "✅"
    except ImportError:
        deps["wakeword"] = "⚠️ 未安装 (pip install openwakeword)"
    
    # silero-vad
    try:
        import torch
        deps["vad"] = "✅"
    except ImportError:
        deps["vad"] = "⚠️ silero-vad 未安装"
    
    return deps


def print_dependencies(deps):
    print("\n" + "="*50)
    print("  Jarvis Voice Agent — 依赖检查")
    print("="*50)
    for name, status in deps.items():
        print(f"  {name:<12} {status}")
    print("="*50 + "\n")


# ==================== 音频工具 ====================

def get_audio_devices():
    """列出可用的音频输入设备"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        inputs = [d for d in devices if d['max_input_channels'] > 0]
        print(f"\n可用麦克风 ({len(inputs)} 个):")
        for i, d in enumerate(inputs):
            print(f"  [{i}] {d['name']} (输入通道: {d['max_input_channels']})")
        return inputs
    except ImportError:
        print("sounddevice 未安装，无法列出设备")
        return []


class AudioCapture:
    """音频采集器 — 持续从麦克风读取音频"""
    
    def __init__(self, device=None, sample_rate=SAMPLE_RATE, chunk_size=CHUNK_SIZE):
        self.device = device
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.running = False
        self.stream = None
        
    def start(self):
        import sounddevice as sd
        self.running = True
        q = queue.Queue()
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio capture: {status}")
            q.put(indata.copy())
        
        self.stream = sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=callback
        )
        self.stream.start()
        logger.info(f"音频采集开始 (设备: {self.device}, 采样率: {self.sample_rate})")
        return q
    
    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("音频采集停止")


# ==================== VAD — 语音活动检测 ====================
class RNNoiseDenoiser:
    """RNNoise 降噪处理器 - 自动降级到 noisereduce"""

    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.model = None
        self._loaded = False
        self.engine = None  # 'rnnoise' or 'noisereduce'
        self.load_model()

    def load_model(self):
        """加载 RNNoise 模型，失败则尝试 noisereduce"""
        import numpy as np
        # 先尝试 RNNoise
        try:
            from pyrnnoise import RNNoise
            self.model = RNNoise(sample_rate=self.sample_rate)
            self._loaded = True
            self.engine = 'rnnoise'
            logger.info("RNNoise 降噪模型加载成功")
            return self._loaded
        except ImportError:
            pass

        # RNNoise 失败，尝试 noisereduce
        try:
            import noisereduce as nr
            self.model = nr
            self._loaded = True
            self.engine = 'noisereduce'
            logger.info("noisereduce 降噪加载成功 (RNNoise 不可用，已降级)")
            return self._loaded
        except ImportError:
            logger.warning("pyrnnoise 和 noisereduce 都未安装，跳过降噪")
            self._loaded = False
            return False

        except Exception as e:
            logger.warning(f"降噪加载失败: {e}")
            self._loaded = False
            return False
    
    def denoise(self, audio, sample_rate=16000):
        """对音频进行降噪"""
        if not self._loaded or self.model is None:
            return audio

        if self.engine == 'rnnoise':
            # RNNoise 原生分帧处理
            import numpy as np
            # RNNoise 需要 16kHz 单通道 float32
            if sample_rate != 16000:
                logger.warning("RNNoise 仅支持 16kHz 采样率")
                return audio

            # 分块处理
            frame_size = 480  # RNNoise 标准帧大小
            result = np.zeros_like(audio)

            for i in range(0, len(audio), frame_size):
                frame = audio[i:i+frame_size]
                if len(frame) < frame_size:
                    # 补齐最后一帧
                    padded = np.zeros(frame_size, dtype=np.float32)
                    padded[:len(frame)] = frame
                    denoised = self.model.denoise_frame(padded)
                    result[i:i+len(frame)] = denoised[:len(frame)]
                else:
                    result[i:i+frame_size] = self.model.denoise_frame(frame)

            return result

        elif self.engine == 'noisereduce':
            # noisereduce 谱减法降噪
            import numpy as np
            # noisereduce 需要 float64
            audio_float = audio.astype(np.float64)
            # 估计前 0.5 秒作为噪声
            noise_samples = int(0.5 * sample_rate)
            if len(audio_float) > noise_samples:
                noise_profile = audio_float[:noise_samples]
                reduced = self.model.reduce_noise(
                    y=audio_float,
                    y_noise=noise_profile,
                    sr=sample_rate
                )
            else:
                # 太短，直接返回
                reduced = audio_float
            return reduced.astype(np.float32)

        return audio


# ==================== 参数动态自适应 (多尺度能量版) ====================
# DeepSeek V4 DSA启发: 动态稀疏化 - 只在需要时精细处理
# 多尺度能量跟踪: 短窗口捕捉瞬时爆发, 长窗口估计噪声底噪

class AdaptiveThreshold:
    """动态自适应阈值调整 — 多尺度能量版
    
    DeepSeek V4 启发:
    - 类似DSA的动态稀疏化：噪声平稳期用大窗口低负载，语音活跃期自动精细化
    - 多尺度能量融合：短(10ms)捕捉瞬时爆发, 中(50ms)平滑过渡, 长(200ms)估计底噪
    """
    
    def __init__(
        self,
        initial_threshold: float = 0.02,
        alpha: float = 0.95,
        noise_window_size: int = 100,
        sample_rate: int = 16000
    ) -> None:
        self.threshold: float = initial_threshold
        self.alpha: float = alpha  # 平滑系数
        self.noise_window_size: int = noise_window_size
        self.current_noise_floor: float = 0.0
        self.sample_rate: int = sample_rate
        
        # 多尺度能量历史 (稀疏处理核心)
        # short_scale: 10ms 窗口, 捕捉瞬时爆发
        # mid_scale: 50ms 窗口, 平滑过渡
        # long_scale: 200ms 窗口, 噪声底噪估计
        self.short_history: list[float] = []
        self.mid_history: list[float] = []
        self.long_history: list[float] = []
        
        # 窗口大小(样本数)
        self.short_win = int(0.010 * sample_rate)   # 10ms
        self.mid_win = int(0.050 * sample_rate)     # 50ms
        self.long_win = int(0.200 * sample_rate)     # 200ms
        
        # 累积缓冲用于计算多尺度能量
        self.sample_buffer: list[float] = []
        self.buffer_max_len = self.long_win  # 缓冲最大200ms
        
        # 活跃度指示 (稀疏处理开关)
        self.activity_level: str = "idle"  # idle | moderate | active
        self.sparse_mode: bool = True  # True=稀疏模式(大窗口), False=精细模式
        
        # 动态阈值参数
        self.short_weight: float = 0.3   # 短窗口权重(瞬时爆发敏感)
        self.long_weight: float = 0.7   # 长窗口权重(底噪估计稳定)
        
    def update(self, chunk_energy: float) -> None:
        """更新多尺度能量并调整阈值
        
        DeepSeek V4 DSA启发: 
        - 稀疏更新：每帧不一定重新计算所有尺度，按需精细化
        """
        import numpy as np
        
        # 累积样本到缓冲
        self.sample_buffer.append(chunk_energy)
        if len(self.sample_buffer) > self.buffer_max_len:
            self.sample_buffer.pop(0)
        
        # 多尺度能量计算
        buf_len = len(self.sample_buffer)
        
        # 短窗口能量(最后10ms或全部如果不足)
        short_samples = min(buf_len, self.short_win)
        short_energy = np.mean(self.sample_buffer[-short_samples:]) if short_samples > 0 else chunk_energy
        
        # 中窗口能量(最后50ms)
        mid_samples = min(buf_len, self.mid_win)
        mid_energy = np.mean(self.sample_buffer[-mid_samples:]) if mid_samples > 0 else chunk_energy
        
        # 长窗口能量(最后200ms, 用于噪声底噪估计)
        long_samples = min(buf_len, self.long_win)
        long_energy = np.mean(self.sample_buffer[-long_samples:]) if long_samples > 0 else chunk_energy
        
        # 更新各尺度历史
        self.short_history.append(short_energy)
        self.mid_history.append(mid_energy)
        self.long_history.append(long_energy)
        
        # 保持滑动窗口
        max_hist = max(self.noise_window_size, self.mid_win)
        for hist_list in [self.short_history, self.mid_history, self.long_history]:
            while len(hist_list) > max_hist:
                hist_list.pop(0)
        
        # 计算当前噪声底噪(使用长窗口平均)
        if len(self.long_history) > 0:
            self.current_noise_floor = float(np.mean(self.long_history[-self.noise_window_size:]))
        
        # 判断活跃度等级 (稀疏处理开关)
        if len(self.mid_history) >= 10:
            recent_avg = np.mean(self.mid_history[-10:])
            if recent_avg < self.current_noise_floor * 1.5:
                self.activity_level = "idle"
                self.sparse_mode = True
            elif recent_avg < self.current_noise_floor * 3:
                self.activity_level = "moderate"
                self.sparse_mode = False  # 需要精细处理
            else:
                self.activity_level = "active"
                self.sparse_mode = False
        
        # 多尺度融合阈值
        # 短窗口检测瞬时爆发, 长窗口确认持续语音
        # 融合公式: threshold = long_floor * 2.5 + short_spike_bonus
        short_spike = short_energy - self.current_noise_floor
        short_spike_bonus = max(0, short_spike) * self.short_weight
        
        self.threshold = max(
            0.01, 
            self.current_noise_floor * 2.5 + short_spike_bonus + 0.01
        )

    def get_threshold(self) -> float:
        return self.threshold
    
    def get_multi_scale_energy(self) -> dict:
        """返回当前多尺度能量(用于VAD融合)"""
        import numpy as np
        return {
            "short": np.mean(self.short_history[-5:]) if len(self.short_history) >= 5 else 0.0,
            "mid": np.mean(self.mid_history[-5:]) if len(self.mid_history) >= 5 else 0.0,
            "long": self.current_noise_floor,
            "activity": self.activity_level,
            "sparse": self.sparse_mode,
        }


# ==================== 两级串联检测 (VAD + 唤醒词) ====================

import numpy as np
from typing import Optional, Union, List

class TwoStageDetector:
    """VAD + 唤醒词 两级串联检测
    
    DeepSeek V4 稀疏注意力启发整合:
    - MultiScaleEnergyVAD: 多尺度能量VAD替代简单能量检测
    - AdaptiveThreshold: 多尺度自适应阈值替代单尺度
    - RNNoise: 实时降噪,只在需要时精细处理
    - 稀疏处理: idle时大窗口低负载, active时精细融合
    """
    
    def __init__(self, wakeword_threshold: float = 0.5, sample_rate: int = 16000) -> None:
        self.vad_model = None
        self.get_speech_timestamps = None
        self.wakeword_model = None
        self.wakeword_threshold: float = wakeword_threshold
        self.sample_rate = sample_rate
        
        # 多尺度自适应阈值
        self.adaptive_threshold: AdaptiveThreshold = AdaptiveThreshold(
            initial_threshold=0.02,
            noise_window_size=100,
            sample_rate=sample_rate
        )
        
        # 多尺度能量VAD (替代SimpleVAD)
        self.multi_scale_vad: MultiScaleEnergyVAD = MultiScaleEnergyVAD(
            threshold=0.02,
            min_speech_samples=int(0.3 * sample_rate),  # 300ms最小语音
            sample_rate=sample_rate,
            short_window_ms=0.010,
            mid_window_ms=0.050,
            long_window_ms=0.200,
            short_weight=0.4,
            long_weight=0.6,
        )
        
        # RNNoise降噪
        self.denoiser: RNNoiseDenoiser = RNNoiseDenoiser(sample_rate=sample_rate)
        
        # 语音缓冲
        self.speech_buffer: List[np.ndarray] = []
        self.is_speaking: bool = False
        
        # 稀疏处理状态
        self.processing_mode: str = "sparse"  # sparse | fine
        
    def initialize(self) -> 'TwoStageDetector':
        """初始化所有组件"""
        # 加载 Silero VAD
        try:
            import torch
            torch.device("mps")
            self.vad_model, self.get_speech_timestamps = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                trust_repo=True
            )
            logger.info("Silero VAD 加载成功")
        except Exception as e:
            logger.warning(f"Silero VAD 加载失败: {e}")
            
        # 加载 RNNoise 降噪
        self.denoiser.load_model()
        
        # 唤醒词模型会在外部分加载
        return self
        
    def set_wakeword_model(self, model) -> None:
        """设置唤醒词模型"""
        self.wakeword_model = model

    def process_chunk(
        self,
        chunk: np.ndarray,
        sample_rate: int = 16000
    ) -> Optional[Union[bool, np.ndarray]]:
        """处理音频块，返回检测结果：
        None - 无语音
        True - 检测到唤醒词，需要处理完整语音
        speech_data - 语音结束，返回处理好的语音数据
        """
        import numpy as np
        
        # 更新多尺度自适应阈值
        energy = np.abs(chunk).mean()
        self.adaptive_threshold.update(energy)
        current_threshold = self.adaptive_threshold.get_threshold()
        noise_floor = self.adaptive_threshold.current_noise_floor
        
        # 获取多尺度能量状态(用于稀疏处理决策)
        ms_energy = self.adaptive_threshold.get_multi_scale_energy()
        
        # 更新VAD的稀疏处理模式
        self.multi_scale_vad.activity_state = ms_energy["activity"]
        self.multi_scale_vad.sparse_mode = ms_energy["sparse"]
        self.processing_mode = "fine" if not ms_energy["sparse"] else "sparse"
        
        # 稀疏处理: idle状态降低RNNoise调用频率
        if ms_energy["sparse"]:
            # 稀疏模式: 只做基本能量检测, 跳过RNNoise
            if energy > current_threshold:
                self.speech_buffer.append(chunk)
                if len(np.concatenate(self.speech_buffer)) >= int(1.5 * sample_rate):
                    return self._finalize_speech(sample_rate)
                self.is_speaking = True
                return None
            else:
                if self.is_speaking and len(np.concatenate(self.speech_buffer)) >= int(0.5 * sample_rate):
                    return self._finalize_speech(sample_rate)
                elif len(self.speech_buffer) > 0:
                    self.speech_buffer = []
                    self.is_speaking = False
                return None
        
        # 精细模式: 启用多尺度VAD + RNNoise
        # 第一级: 多尺度能量VAD
        vad_result = self.multi_scale_vad.process(chunk, noise_floor)
        
        if vad_result is True:
            # VAD检测到语音开始，继续累积
            if len(self.speech_buffer) == 0:
                # 第一个语音块，启用RNNoise
                if self.denoiser._loaded:
                    chunk = self.denoiser.denoise(chunk, sample_rate)
            self.speech_buffer.append(chunk)
            self.is_speaking = True
            return None
            
        elif isinstance(vad_result, np.ndarray):
            # 语音结束，返回完整语音
            self.speech_buffer.append(chunk)  # 加入最后的静音前的一块
            return self._finalize_speech(sample_rate)
        
        # 多尺度VAD未触发，使用能量检测作为后备
        if energy > current_threshold:
            # RNNoise 降噪(精细模式)
            if self.denoiser._loaded:
                chunk = self.denoiser.denoise(chunk, sample_rate)
            self.speech_buffer.append(chunk)
            
            if len(np.concatenate(self.speech_buffer)) >= int(1.5 * sample_rate):
                # 检查唤醒词
                if self.wakeword_model is not None:
                    full_audio = np.concatenate(self.speech_buffer)
                    if self._detect_wakeword(full_audio):
                        logger.info(f"✅ 唤醒词检测成功 (阈值: {current_threshold:.4f})")
                        return True
                else:
                    return True
            self.is_speaking = True
            return None
            
        else:
            # 静音
            if self.is_speaking and len(np.concatenate(self.speech_buffer)) >= int(0.5 * sample_rate):
                return self._finalize_speech(sample_rate)
            elif len(self.speech_buffer) > 0:
                self.speech_buffer = []
                self.is_speaking = False
            return None
    
    def _finalize_speech(self, sample_rate: int) -> Optional[np.ndarray]:
        """完成语音处理: 合并缓冲 + 最终RNNoise降噪"""
        import numpy as np
        if not self.speech_buffer:
            return None
        
        speech_data = np.concatenate(self.speech_buffer).astype(np.float32)
        
        # 最终RNNoise降噪
        if self.denoiser._loaded and len(speech_data) > 0:
            speech_data = self.denoiser.denoise(speech_data, sample_rate)
        
        self.speech_buffer = []
        self.is_speaking = False
        return speech_data
            
    def _detect_wakeword(self, audio):
        """用唤醒词模型检测"""
        if self.wakeword_model is None:
            return False
            
        try:
            predictions = self.wakeword_model.predict(audio)
            for key, score in predictions.items():
                if score > self.wakeword_threshold:
                    logger.debug(f"唤醒词得分 {key}: {score:.3f}")
                    return True
            return False
        except Exception as e:
            logger.warning(f"唤醒词检测错误: {e}")
            return False
            
    def get_buffer(self) -> Optional[np.ndarray]:
        """获取当前缓冲"""
        import numpy as np
        if not self.speech_buffer:
            return None
        return np.concatenate(self.speech_buffer).astype(np.float32) if len(self.speech_buffer) > 0 else None
    
    def get_processing_mode(self) -> str:
        """获取当前处理模式(sparse/fine)"""
        return self.processing_mode


# ==================== 多尺度能量VAD (DeepSeek V4稀疏注意力启发) ====================
# 核心思路: 类似稀疏注意力 — 平稳期稀疏处理(大窗口低负载), 活跃期精细处理
# 短窗口捕捉瞬时爆发 + 长窗口确认持续语音 = 多尺度融合

class MultiScaleEnergyVAD:
    """多尺度能量VAD — 稀疏注意力风格的语音活动检测
    
    DeepSeek V4 多尺度特征融合启发:
    - short_window(10ms): 捕捉瞬时能量爆发, 对突发语音敏感
    - mid_window(50ms): 平滑过渡, 区分语音和瞬时噪声
    - long_window(200ms): 确认持续语音, 噪声底噪估计
    
    稀疏处理:
    - idle状态: 降低采样率, 用大窗口稀疏检测
    - active状态: 全采样率, 多尺度精细融合
    """
    
    def __init__(
        self,
        threshold: float = 0.02,
        min_speech_samples: int = 4800,
        sample_rate: int = 16000,
        # 多尺度窗口配置
        short_window_ms: float = 0.010,   # 10ms 短窗口
        mid_window_ms: float = 0.050,     # 50ms 中窗口
        long_window_ms: float = 0.200,     # 200ms 长窗口
        # 融合权重
        short_weight: float = 0.4,         # 短窗口权重(瞬时爆发)
        long_weight: float = 0.6,          # 长窗口权重(持续确认)
    ):
        self.threshold = threshold
        self.min_speech_samples = min_speech_samples
        self.sample_rate = sample_rate
        self.short_window_ms = short_window_ms
        self.mid_window_ms = mid_window_ms
        self.long_window_ms = long_window_ms
        self.short_weight = short_weight
        self.long_weight = long_weight
        
        # 窗口大小(样本数)
        self.short_win = int(short_window_ms * sample_rate)
        self.mid_win = int(mid_window_ms * sample_rate)
        self.long_win = int(long_window_ms * sample_rate)
        
        # 状态
        self.speech_buffer: List[float] = []
        self.is_speaking = False
        
        # 多尺度能量缓冲
        self.energy_buffer: List[float] = []  # 原始能量序列
        self.buffer_max_len = self.long_win  # 最多200ms的能量数据
        
        # 活跃度状态 (稀疏处理开关)
        self.activity_state: str = "idle"  # idle | moderate | active
        self.sparse_mode: bool = True
        
        # 检测参数
        self.speech_confidence: float = 0.0  # 语音置信度
        self.confidence_threshold: float = 0.6  # 触发阈值
        
    def _compute_multi_scale_energy(self, chunk: np.ndarray) -> dict:
        """计算多尺度能量"""
        import numpy as np
        energy = float(np.abs(chunk).mean())
        
        # 累积到能量缓冲
        self.energy_buffer.append(energy)
        if len(self.energy_buffer) > self.buffer_max_len:
            self.energy_buffer.pop(0)
        
        buf_len = len(self.energy_buffer)
        
        # 短窗口能量(最后10ms)
        short_n = min(buf_len, self.short_win)
        short_energy = np.mean(self.energy_buffer[-short_n:]) if short_n > 0 else energy
        
        # 中窗口能量(最后50ms)
        mid_n = min(buf_len, self.mid_win)
        mid_energy = np.mean(self.energy_buffer[-mid_n:]) if mid_n > 0 else energy
        
        # 长窗口能量(最后200ms)
        long_n = min(buf_len, self.long_win)
        long_energy = np.mean(self.energy_buffer[-long_n:]) if long_n > 0 else energy
        
        return {
            "instant": energy,
            "short": short_energy,
            "mid": mid_energy,
            "long": long_energy,
        }
    
    def _fuse_multi_scale(self, energies: dict, noise_floor: float) -> float:
        """多尺度融合得分
        
        DeepSeek V4 融合思路:
        - 短窗口权重捕捉瞬时爆发
        - 长窗口权重确认持续语音
        - 只有两者都超过阈值才判定为语音(避免瞬时噪声误触发)
        """
        short_score = max(0, energies["short"] - noise_floor)
        long_score = max(0, energies["long"] - noise_floor)
        
        # 融合: 短*短权重 + 长*长权重
        fused = short_score * self.short_weight + long_score * self.long_weight
        
        # 活跃度加权: active时提高短权重(敏感), idle时提高长权重(稳定)
        if self.activity_state == "active":
            fused = energies["short"] * 0.6 + energies["long"] * 0.4 - noise_floor
        elif self.activity_state == "idle":
            fused = energies["short"] * 0.2 + energies["long"] * 0.8 - noise_floor
        
        return max(0, fused)
    
    def _update_activity_state(self, energies: dict, noise_floor: float) -> None:
        """更新活跃度状态(稀疏处理开关)"""
        ratio = energies["mid"] / max(noise_floor, 0.001)
        
        if ratio < 1.5:
            self.activity_state = "idle"
            self.sparse_mode = True
        elif ratio < 3.0:
            self.activity_state = "moderate"
            self.sparse_mode = False
        else:
            self.activity_state = "active"
            self.sparse_mode = False
    
    def process(self, audio_chunk: np.ndarray, noise_floor: float = 0.01) -> Optional[Union[bool, np.ndarray]]:
        """检测语音活动
        
        Returns:
            True: 语音开始
            np.ndarray: 语音结束，返回完整语音数据
            None: 继续检测
        """
        import numpy as np
        
        # 计算多尺度能量
        energies = self._compute_multi_scale_energy(audio_chunk)
        
        # 更新活跃度状态
        self._update_activity_state(energies, noise_floor)
        
        # 多尺度融合得分
        confidence = self._fuse_multi_scale(energies, noise_floor)
        self.speech_confidence = confidence
        
        # 稀疏处理: idle状态用更简单的检测逻辑
        if self.sparse_mode and self.activity_state == "idle":
            # 稀疏模式: 用instant能量判断当前帧 + long窗口确认持续语音
            # bugfix: 原来只检查long窗口，忽略了当前帧的instant能量，导致漏检
            if energies["instant"] > noise_floor * 3.0 and energies["long"] > noise_floor * 1.5:
                self.speech_buffer.extend(audio_chunk.tolist())
                if len(self.speech_buffer) >= self.min_speech_samples:
                    self.is_speaking = True
                    return True
            else:
                # idle状态清除缓冲
                if not self.is_speaking:
                    self.speech_buffer = []
            return None
        
        # 精细模式: 使用融合得分判断
        if confidence > self.confidence_threshold:
            self.speech_buffer.extend(audio_chunk.tolist())
            self.is_speaking = True
            return None  # 继续累积
            
        # 静音或低能量
        if self.is_speaking and len(self.speech_buffer) >= self.min_speech_samples:
            # 语音结束
            speech = np.array(self.speech_buffer, dtype=np.float32)
            self.speech_buffer = []
            self.is_speaking = False
            return speech
        else:
            # 太短，丢弃
            self.speech_buffer = []
            self.is_speaking = False
        return None
    
    def get_audio(self) -> Optional[np.ndarray]:
        """获取累积的语音数据"""
        import numpy as np
        if len(self.speech_buffer) >= self.min_speech_samples:
            speech = np.array(self.speech_buffer, dtype=np.float32)
            self.speech_buffer = []
            self.is_speaking = False
            return speech
        self.speech_buffer = []
        self.is_speaking = False
        return None
    
    def get_status(self) -> dict:
        """获取VAD状态"""
        return {
            "is_speaking": self.is_speaking,
            "activity_state": self.activity_state,
            "sparse_mode": self.sparse_mode,
            "confidence": self.speech_confidence,
            "buffer_samples": len(self.speech_buffer),
        }


class SimpleVAD:
    """简单的能量检测 VAD（备用/降级模式）"""
    
    def __init__(self, threshold=0.02, min_speech_samples=4800):
        self.threshold = threshold
        self.min_speech_samples = min_speech_samples
        self.speech_buffer = []
        self.is_speaking = False
        
    def process(self, audio_chunk):
        """检测是否有语音"""
        import numpy as np
        energy = np.abs(audio_chunk).mean()
        
        if energy > self.threshold:
            self.speech_buffer.extend(audio_chunk.tolist())
            if len(self.speech_buffer) >= self.min_speech_samples:
                self.is_speaking = True
                return True
        else:
            if self.is_speaking and len(self.speech_buffer) > self.min_speech_samples:
                # 语音结束
                speech = self.speech_buffer.copy()
                self.speech_buffer = []
                self.is_speaking = False
                return speech
            self.speech_buffer = []
            self.is_speaking = False
        return None
    
    def get_audio(self):
        """获取累积的语音数据"""
        if len(self.speech_buffer) >= self.min_speech_samples:
            speech = self.speech_buffer.copy()
            self.speech_buffer = []
            self.is_speaking = False
            return speech
        return None


def load_silero_vad():
    """加载 Silero VAD 模型"""
    try:
        import torch
        torch.device("mps")
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            trust_repo=True
        )
        get_speech_timestamps = utils[0]
        return model, get_speech_timestamps
    except Exception as e:
        logger.warning(f"Silero VAD 加载失败: {e}")
        return None, None


# ==================== STT — Whisper ====================

def transcribe_with_whisper(audio_data, sample_rate=SAMPLE_RATE):
    """用 mlx_whisper 转写音频"""
    import mlx_whisper
    import tempfile
    
    # 保存为临时 wav 文件
    import numpy as np
    import wave
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wav_path = f.name
        # 转换 float32 到 int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        with wave.open(wav_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.writeframes(audio_int16.tobytes())
    
    try:
        result = mlx_whisper.transcribe(wav_path, language="zh")
        text = result.get("text", "").strip()
        return text if text else None
    finally:
        os.unlink(wav_path)


# ==================== LLM — Qwen3.5 流式推理 ====================

def stream_chat(message, system_prompt=None, model=DEFAULT_MODEL):
    """流式对话 — 生成器，过滤Qwen3.5 thinking思考过程
    
    Qwen3.5 thinking 模式处理：
    - 情况1：思考过程在 reasoning_content，回答在 content → 过滤 reasoning_content
    - 情况2：思考过程直接写在 content 里 → 检测并跳过直到 "Final Answer"
    - 情况3：流式时只有 reasoning_content，content 在最后 → 最后获取完整 content
    """
    import requests
    import json
    
    if system_prompt is None:
        system_prompt = "你是一个友好、有帮助的AI助手。请用简洁的中文回答。"
    
    url = f"{OMLX_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": OMLX_AUTH,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "max_tokens": 512,
        "stream": True,
    }
    
    thinking_buffer = ""
    found_final_answer = False
    has_seen_content = False
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if not line or line.startswith(b": "):
                continue
            if line.startswith(b"data: "):
                data = line[6:]
                if data.strip() == b"[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    
                    # Qwen3.5 thinking 模式：情况1 - 推理在 reasoning_content → 全部过滤
                    reasoning = delta.get("reasoning_content")
                    if reasoning:
                        thinking_buffer += reasoning
                        # 过滤掉思考过程，不输出
                        pass
                    
                    # 检查是否有 content
                    content = delta.get("content")
                    if content:
                        has_seen_content = True
                        if not found_final_answer:
                            thinking_buffer += content
                            # 检测各种回答开始标记
                            if "**Final Answer:**" in thinking_buffer or \
                               "最终答案：" in thinking_buffer or \
                               "答案：" in thinking_buffer or \
                               "回答：" in thinking_buffer:
                                found_final_answer = True
                                # 提取标记后的内容
                                for marker in ["**Final Answer:**", "最终答案：", "答案：", "回答："]:
                                    if marker in thinking_buffer:
                                        idx = thinking_buffer.find(marker) + len(marker)
                                        final_content = thinking_buffer[idx:]
                                        if final_content.strip():
                                            yield final_content
                                        break
                            continue
                        else:
                            # 已经找到 Final Answer，正常输出
                            yield content
                    
                except json.JSONDecodeError:
                    continue
        
        # 流式结束后特殊处理：如果只收到 reasoning_content，重新获取完整回答
        if not has_seen_content:
            # 重新发起非流式请求
            payload["stream"] = False
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            message = result["choices"][0]["message"]
            content = message.get("content", "")
            
            # 如果思考过程混在 content 中，提取 Final Answer
            if content and ("Thinking Process:" in content or "**Final Answer:**" in content or "最终答案：" in content):
                markers = ["**Final Answer:**", "最终答案：", "答案：", "回答："]
                for marker in markers:
                    if marker in content:
                        idx = content.find(marker) + len(marker)
                        content = content[idx:]
                        break
                content = content.strip()
            
            if content.strip():
                yield content
        elif has_seen_content and not found_final_answer:
            # 已经收到 content，但全程没找到 Final Answer 标记
            # 这种情况就是：思考在 reasoning_content，回答直接在 content → 直接返回收集到的全部 content
            content = thinking_buffer.strip()
            if content:
                yield content
                    
    except Exception as e:
        logger.error(f"LLM 流式推理错误: {e}")
        yield f"[错误: {e}]"


def chat_once(message, system_prompt=None, model=DEFAULT_MODEL, max_tokens=512):
    """单次对话（非流式），过滤思考过程"""
    import requests
    import json
    
    if system_prompt is None:
        system_prompt = "你是一个友好、有帮助的AI助手。请用简洁的中文回答。"
    
    url = f"{OMLX_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": OMLX_AUTH,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "max_tokens": max_tokens,
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        message = result["choices"][0]["message"]
        
        # Qwen3.5 thinking 模式处理：
        # 情况1：思考过程在 reasoning_content，回答在 content
        content = message.get("content", "")
        reasoning = message.get("reasoning_content")
        
        # 如果思考过程混在 content 中，需要提取 Final Answer
        if content and ("Thinking Process:" in content or "**Final Answer:**" in content or "最终答案：" in content):
            # 查找答案开始标记
            markers = ["**Final Answer:**", "最终答案：", "答案：", "回答："]
            for marker in markers:
                if marker in content:
                    idx = content.find(marker) + len(marker)
                    content = content[idx:]
                    break
        
        content = content.strip()
        return content if content else "[无响应]"
    except Exception as e:
        logger.error(f"LLM 对话错误: {e}")
        return f"[错误: {e}]"


# ==================== TTS — Kokoro ====================

def speak_text_streaming(text, voice=DEFAULT_VOICE, output_dir=OUTPUT_DIR):
    """
    流式 TTS: 分段生成并播放音频
    返回生成器，每次 yield (chunk_audio, is_final)
    """
    from mlx_audio.tts.generate import generate_audio
    import numpy as np
    import tempfile
    import wave
    import subprocess
    import struct
    
    # 清理文本
    text = text.strip()
    if not text:
        return
    
    # 生成完整音频
    timestamp = int(time.time())
    output_path = output_dir / f"response_{timestamp}"
    
    try:
        generate_audio(
            text=text,
            model_path=KOKORO_MODEL,
            voice=voice,
            file_prefix=str(output_path),
            audio_format="wav",
        )
        
        # 读取生成的音频
        wav_file = f"{output_path}.wav"
        if os.path.exists(wav_file):
            # 返回文件路径让调用者播放
            yield wav_file, True
            
    except Exception as e:
        logger.error(f"TTS 生成错误: {e}")
        yield None, False


def speak_text(text, voice=DEFAULT_VOICE, output_dir=OUTPUT_DIR):
    """同步 TTS 生成并播放"""
    for audio_file, _ in speak_text_streaming(text, voice, output_dir):
        if audio_file:
            # 用 ffplay 播放（后台）
            try:
                proc = subprocess.Popen([
                    "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                track_playback_process(proc)
                logger.info(f"🔊 播放: {audio_file}")
            except Exception as e:
                logger.error(f"播放失败: {e}")


# ==================== 唤醒词检测 ====================

def load_wakeword_model():
    """加载唤醒词检测模型"""
    try:
        from openwakeword.model import Model
        import warnings
        warnings.filterwarnings("ignore")
        
        model = Model()
        logger.info("唤醒词模型加载完成")
        return model
    except Exception as e:
        logger.warning(f"唤醒词模型加载失败: {e}")
        return None


def detect_wakeword(model, audio_chunk, threshold=0.5):
    """检测唤醒词"""
    if model is None:
        return False
    
    try:
        predictions = model.predict(audio_chunk)
        for key, score in predictions.items():
            if score > threshold and any(kw in key.lower() for kw in ["yuanfang", "唤醒", "hello"]):
                return True
    except Exception:
        pass
    return False


# ==================== 主循环 ====================

def audio_to_numpy(audio_queue, running, sample_rate=SAMPLE_RATE, chunk_size=CHUNK_SIZE):
    """把音频队列转为 numpy 数组"""
    import numpy as np
    
    all_audio = []
    while running.value:
        try:
            chunk = audio_queue.get(timeout=0.1)
            all_audio.append(chunk)
        except queue.Empty:
            continue
    
    if all_audio:
        return np.concatenate(all_audio).flatten()
    return np.array([])


def run_jarvis_loop(
    wakeword_enabled: bool = False,
    continuous: bool = True,
    verbose: bool = False
) -> None:
    """
    Jarvis 主循环
    
    Args:
        wakeword_enabled: 是否使用唤醒词模式（否则持续监听）
        continuous: 是否持续监听（False 则单次交互）
        verbose: 详细输出
    """
    import numpy as np
    import sounddevice as sd
    
    logger.info("="*50)
    logger.info("  Jarvis Voice Agent 启动")
    logger.info("  优化: 多尺度能量VAD + 稀疏处理 + 自适应阈值 + RNNoise降噪 + 端侧STT")
    logger.info("  DeepSeek V4启发: 稀疏注意力(按需精细化) + 多尺度特征融合")
    logger.info("="*50)
    
    # 加载模型
    # 两级串联检测器（包含 VAD + 自适应 + RNNoise）
    two_stage_detector = TwoStageDetector(wakeword_threshold=0.5)
    two_stage_detector.initialize()
    
    # 唤醒词模型
    wakeword_model = load_wakeword_model() if wakeword_enabled else None
    if wakeword_model:
        two_stage_detector.set_wakeword_model(wakeword_model)
    
    # 状态
    is_listening = True
    is_speaking = False
    is_tts_playing = False
    wakeword_detected = False
    conversation_history = []
    system_prompt = """你叫元芳，是于金泽的AI助手。你的任务是"让主人更好地生活"。
保持回答简洁、有帮助。用中文回复。"""

    # 说话打断：跟踪播放中的 ffplay 进程
    import psutil
    def kill_all_tts():
        """杀掉所有正在播放TTS的ffplay进程，实现说话打断"""
        killed = 0
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] in ('ffplay', 'ffplay.bin'):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        global is_tts_playing
        if killed > 0:
            logger.info(f"🔪 说话打断：已停止 {killed} 个TTS播放进程")
            is_tts_playing = False
        return killed

    logger.info("🎤 持续监听中... (Ctrl+C 退出)")
    logger.info(f"   唤醒词模式: {'开启 ✅' if wakeword_enabled else '关闭'}")
    logger.info(f"   持续对话: {'开启 ✅' if continuous else '关闭'}")
    logger.info(f"   RNNoise降噪: {'开启 ✅' if two_stage_detector.denoiser._loaded else '未安装/关闭'}")
    logger.info(f"   说话打断: 开启 ✅ (检测到说话即停止当前TTS播放)")
    
    # 自动探测可用音频输入设备
    # 默认设备可能是 -1（表示未设置），需要自动选择第一个可用输入设备
    input_device = None
    devices = sd.query_devices()
    input_devices = [i for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
    if input_devices:
        input_device = input_devices[0]
        logger.info(f"使用音频输入设备 #{input_device}: {devices[input_device]['name']}")
    else:
        logger.warning("未找到可用音频输入设备，使用默认配置")
    
    # 创建音频流
    q: queue.Queue[np.ndarray] = queue.Queue()
    
    def callback(indata, frames, time, status):
        if status:
            if verbose:
                logger.warning(f"Audio: {status}")
        q.put(indata.copy())
    
    try:
        with sd.InputStream(device=input_device, channels=1, samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, callback=callback) as stream:
            logger.info(f"音频流已启动 (设备: {stream.device})")
            
            # 语音识别结果
            current_transcript = ""
            full_response = ""
            speech_buffer: List[np.ndarray] = []
            detection_active = wakeword_enabled  # 如果开启唤醒词，一开始只检测唤醒词
            
            while True:
                try:
                    chunk = q.get(timeout=0.5)
                    chunk_flat = chunk.flatten()
                    
                    # ========== 说话打断功能 ==========
                    # 如果检测到用户说话且TTS正在播放，立即停止TTS
                    if is_tts_playing:
                        energy = np.abs(chunk_flat).mean()
                        threshold = two_stage_detector.adaptive_threshold.get_threshold()
                        if energy > threshold * 1.5:  # 说话能量比阈值高50%就触发打断
                            killed = kill_all_tts()
                            if killed > 0:
                                # 打断后重置状态，准备采集用户新语音
                                is_speaking = False
                                speech_buffer = []
                                if wakeword_enabled:
                                    detection_active = True
                                continue
                    # ========== /说话打断功能 ==========
                    
                    if wakeword_enabled and detection_active:
                        # 模式1: 只检测唤醒词（两级串联）
                        result = two_stage_detector.process_chunk(chunk_flat, SAMPLE_RATE)
                        
                        if result is True:
                            # 唤醒词检测成功，开始采集完整语音
                            logger.info("🔔 唤醒词已触发，开始聆听...")
                            wakeword_detected = True
                            is_speaking = True
                            detection_active = False
                            buf = two_stage_detector.get_buffer()
                            speech_buffer = buf.tolist() if buf is not None else []
                        elif isinstance(result, np.ndarray):
                            # 语音结束但没检测到唤醒词，继续等待
                            speech_buffer = []
                            continue
                        else:
                            # 继续检测
                            continue
                            
                    elif is_speaking:
                        # 模式2: 唤醒词已触发，正在采集用户语音
                        speech_buffer.append(chunk_flat)
                        # 检查语音是否结束（静音）
                        energy = np.abs(chunk_flat).mean()
                        threshold = two_stage_detector.adaptive_threshold.get_threshold()
                        
                        if energy < threshold and len(speech_buffer) > int(0.5 * SAMPLE_RATE):
                            # 语音结束，开始处理
                            full_audio = np.concatenate(speech_buffer)
                            # RNNoise 最终降噪
                            if two_stage_detector.denoiser._loaded:
                                full_audio = two_stage_detector.denoiser.denoise(full_audio, SAMPLE_RATE)
                            
                            logger.info(f"🗣️ 语音采集完成 ({len(full_audio)/SAMPLE_RATE:.1f}s)")
                            
                            # 端侧 STT (mlx_whisper 本地转写)
                            logger.info("  ⏳ 端侧转写中...")
                            text = transcribe_with_whisper(full_audio, SAMPLE_RATE)
                            
                            if text and len(text.strip()) > 0:
                                logger.info(f"  📝 用户: {text}")
                                
                                # 对话
                                logger.info("  🤖 思考中...")
                                response_text = ""
                                
                                # 流式处理 LLM
                                for token in stream_chat(text, system_prompt):
                                    response_text += token
                                    if verbose:
                                        print(token, end='', flush=True)
                                
                                if verbose:
                                    print()
                                
                                logger.info(f"  💬 助手: {response_text[:100]}...")
                                
                                # TTS 播放
                                logger.info("  🔊 生成语音...")
                                is_tts_playing = True
                                for audio_file, _ in speak_text_streaming(response_text, DEFAULT_VOICE, OUTPUT_DIR):
                                    if audio_file:
                                        import subprocess
                                        proc = subprocess.Popen([
                                            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_file
                                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        proc.wait()  # 等待播放完成
                                        is_tts_playing = False
                                        track_playback_process(proc)
                                        logger.info(f"     播放: {audio_file}")
                                
                                # 保存对话历史
                                conversation_history.append((text, response_text))
                                
                            else:
                                logger.warning("  ⚠️  转写结果为空，跳过")
                            
                            # 重置状态
                            is_speaking = False
                            speech_buffer = []
                            if wakeword_enabled:
                                detection_active = True  # 回到只检测唤醒词模式
                            
                            # 单次交互模式: 完成后退出
                            if not continuous:
                                logger.info("✅ 单次交互完成，退出")
                                break
                            
                        elif energy < threshold and len(speech_buffer) > 200:  # ~4秒
                            # 超时，清空
                            logger.warning(f"  ⏱️  语音超时 ({len(speech_buffer)*CHUNK_SIZE/SAMPLE_RATE:.1f}s)，清空")
                            speech_buffer = speech_buffer[-20:]
                            
                    else:
                        # 无唤醒词模式: 持续检测语音（VAD直接检测）
                        energy = np.abs(chunk_flat).mean()
                        threshold = two_stage_detector.adaptive_threshold.get_threshold()
                        
                        if energy > threshold:
                            # 检测到语音开始
                            if not is_speaking:
                                logger.info("🎤 检测到语音，开始聆听...")
                                is_speaking = True
                            speech_buffer.append(chunk_flat)
                        elif is_speaking and energy < threshold and len(speech_buffer) > int(0.5 * SAMPLE_RATE):
                            # 语音结束，开始处理
                            full_audio = np.concatenate(speech_buffer)
                            # RNNoise 最终降噪
                            if two_stage_detector.denoiser._loaded:
                                full_audio = two_stage_detector.denoiser.denoise(full_audio, SAMPLE_RATE)
                            
                            logger.info(f"🗣️ 语音采集完成 ({len(full_audio)/SAMPLE_RATE:.1f}s)")
                            
                            # 端侧 STT (mlx_whisper 本地转写)
                            logger.info("  ⏳ 端侧转写中...")
                            text = transcribe_with_whisper(full_audio, SAMPLE_RATE)
                            
                            if text and len(text.strip()) > 0:
                                logger.info(f"  📝 用户: {text}")
                                
                                # 对话
                                logger.info("  🤖 思考中...")
                                response_text = ""
                                
                                # 流式处理 LLM
                                for token in stream_chat(text, system_prompt):
                                    response_text += token
                                    if verbose:
                                        print(token, end='', flush=True)
                                
                                if verbose:
                                    print()
                                
                                logger.info(f"  💬 助手: {response_text[:100]}...")
                                
                                # TTS 播放
                                logger.info("  🔊 生成语音...")
                                is_tts_playing = True
                                for audio_file, _ in speak_text_streaming(response_text, DEFAULT_VOICE, OUTPUT_DIR):
                                    if audio_file:
                                        import subprocess
                                        proc = subprocess.Popen([
                                            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_file
                                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        proc.wait()  # 等待播放完成
                                        is_tts_playing = False
                                        track_playback_process(proc)
                                        logger.info(f"     播放: {audio_file}")
                                
                                # 保存对话历史
                                conversation_history.append((text, response_text))
                                
                            else:
                                logger.warning("  ⚠️  转写结果为空，跳过")
                            
                            # 重置状态（连续对话模式下自动回到聆听状态）
                            is_speaking = False
                            speech_buffer = []
                            
                            # 单次交互模式: 完成后退出
                            if not continuous:
                                logger.info("✅ 单次交互完成，退出")
                                break
                                
                        elif is_speaking and energy < threshold and len(speech_buffer) > 200:  # ~4秒
                            # 超时，清空
                            logger.warning(f"  ⏱️  语音超时 ({len(speech_buffer)*CHUNK_SIZE/SAMPLE_RATE:.1f}s)，清空")
                            speech_buffer = speech_buffer[-20:]
                            
                except queue.Empty:
                    continue
                    
    except KeyboardInterrupt:
        logger.info("\n🛑 退出 Jarvis")
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
        traceback.print_exc()


# ==================== 入口 ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Voice Agent")
    parser.add_argument("--no-wakeword", action="store_true", help="禁用唤醒词，持续监听")
    parser.add_argument("--single", action="store_true", help="单次交互模式")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()
    
    # 检查依赖
    deps = check_dependencies()
    print_dependencies(deps)
    
    if deps["omlx"].startswith("❌"):
        print("❌ OMLX Server 未运行，请先启动:")
        print("   /Applications/oMLX.app/Contents/MacOS/python3 -m omlx.cli serve --base-path ~/.omlx --port 4560")
        sys.exit(1)
    
    # 启动主循环
    run_jarvis_loop(
        wakeword_enabled=not args.no_wakeword,
        continuous=not args.single,
        verbose=args.verbose
    )