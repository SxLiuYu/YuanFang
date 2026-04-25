# routes/wake_word.py
"""
Wake Word Server — WebRTC VAD 语音活动检测 + Porcupine 唤醒词
手机持续推送音频流 → Mac Mini 检测语音/静音 → 触发对话
"""
from flask import Blueprint, request, jsonify
import logging
import struct
import webrtcvad

logger = logging.getLogger(__name__)
wake_bp = Blueprint("wake_word", __name__, url_prefix="/api/wake")

# ==================== WebRTC VAD ====================

class WebRTCVAD:
    """
    WebRTC VAD (Voice Activity Detection)
    支持 16kHz，aggressive=2（平衡模式）
    """
    def __init__(self, sample_rate=16000, aggressive=2, frame_ms=20):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_ms / 1000)  # 320 samples for 20ms @ 16kHz
        self.bytes_per_frame = self.frame_size * 2  # 16-bit = 2 bytes
        self.vad = webrtcvad.Vad(aggressive)
        self.speech_count = 0
        self.silence_count = 0
        self.is_speaking = False
        # 连续3帧语音才确认
        self.min_speech_frames = 3
        # 连续15帧静音才结束
        self.min_silence_frames = 15
        
    def process(self, pcm_data: bytes) -> str:
        """
        处理 PCM 数据（16-bit, 16kHz, mono）
        返回: 'silence' | 'speech' | 'trigger'
        """
        if len(pcm_data) < self.bytes_per_frame:
            return 'silence'
        
        try:
            # WebRTC VAD 只接受特定帧长
            is_speech = self.vad.is_speech(
                pcm_data[:self.bytes_per_frame],
                self.sample_rate
            )
        except:
            return 'silence'
        
        if is_speech:
            self.speech_count += 1
            self.silence_count = 0
            if self.speech_count >= self.min_speech_frames and not self.is_speaking:
                self.is_speaking = True
                return 'trigger'
        else:
            self.silence_count += 1
            if self.is_speaking and self.silence_count >= self.min_silence_frames:
                self.is_speaking = False
                self.speech_count = 0
                
        return 'speech' if self.is_speaking else 'silence'
    
    def reset(self):
        self.speech_count = 0
        self.silence_count = 0
        self.is_speaking = False


# ==================== 全局 VAD 实例 ====================

_vad_instance = None

def get_vad():
    global _vad_instance
    if _vad_instance is None:
        _vad_instance = WebRTCVAD(aggressive=2)
        logger.info("[Wake] WebRTC VAD 初始化完成 (aggressive=2)")
    return _vad_instance


# ==================== 路由 ====================

def init_wake_routes(app):
    app.register_blueprint(wake_bp)
    logger.info(f"[Wake] 路由已注册: /api/wake")


@wake_bp.route("/status", methods=["GET"])
def status():
    """检查唤醒词状态"""
    vad = get_vad()
    return jsonify({
        "method": "webrtc_vad",
        "sample_rate": vad.sample_rate,
        "frame_ms": 20,
        "aggressive": 2,
        "is_speaking": vad.is_speaking,
    })


@wake_bp.route("/vad", methods=["POST"])
def vad_check():
    """
    WebRTC VAD 接口 — 手机推送音频帧，返回是否检测到语音
    
    POST /api/wake/vad
    Content-Type: application/octet-stream
    Body: raw PCM int16 audio (16000Hz mono)
    
    返回: {"status": "silence"|"speech"|"trigger", "is_speaking": bool}
    """
    if not request.data or len(request.data) < 640:
        return jsonify({"error": "audio too short (need >=640 bytes for 20ms)"}), 400
    
    vad = get_vad()
    result = vad.process(request.data)
    return jsonify({
        "status": result,
        "is_speaking": vad.is_speaking,
    })


@wake_bp.route("/vad/reset", methods=["POST"])
def vad_reset():
    """重置 VAD 状态"""
    vad = get_vad()
    vad.reset()
    return jsonify({"status": "reset"})


@wake_bp.route("/test", methods=["GET"])
def test():
    """测试接口"""
    vad = get_vad()
    return jsonify({
        "status": "ok",
        "method": "webrtc_vad",
        "sample_rate": vad.sample_rate,
        "frame_size": vad.frame_size,
        "message": "Send PCM int16 16kHz mono audio to /api/wake/vad",
    })
