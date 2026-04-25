#!/usr/bin/env python3
# scripts/mlx_voice_cli.py
"""
MLX Voice CLI — 快速测试 MLX 语音管线
用法: python scripts/mlx_voice_cli.py <audio_file> [--no-tts]
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.mlx_voice.references import mlx_voice


def main():
    parser = argparse.ArgumentParser(description="MLX Voice 触手 CLI")
    parser.add_argument("audio", help="音频文件路径 (.wav, .mp3, .m4a)")
    parser.add_argument("--no-tts", action="store_true", help="禁用 TTS 语音输出")
    parser.add_argument("--voice", default="af_heart", help="TTS 声音 (默认: af_heart)")
    parser.add_argument("--system", default="你是一个有帮助的AI助手。请用中文回复。", 
                        help="系统提示词")
    args = parser.parse_args()
    
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"❌ 音频文件不存在: {audio_path}")
        sys.exit(1)
    
    print("=" * 50)
    print("MLX Voice 触手")
    print("=" * 50)
    
    # 健康检查
    print("\n📊 组件状态:")
    status = mlx_voice.health_check()
    for component, ok in status.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {component}")
    
    if not status["omlx_server"]:
        print("\n⚠️  OMLX Server 未运行，请先启动:")
        print("    ~/.venv-omlx/bin/omlx serve --model-dir ~/omlx-models/gemma-4-E4B-it-4bit --port 8080")
    
    # 执行管线
    print(f"\n🎤 音频: {audio_path}")
    print(f"🔊 TTS: {'启用' if not args.no_tts else '禁用'}")
    print("-" * 50)
    
    result = mlx_voice.voice_pipeline(
        str(audio_path),
        system_prompt=args.system,
        use_tts=not args.no_tts,
        voice=args.voice,
    )
    
    print("\n" + "=" * 50)
    if result["success"]:
        print("✅ 成功!")
        print(f"\n👤 用户: {result['text']}")
        print(f"\n🤖 助手: {result['response']}")
        if result["audio_file"]:
            print(f"\n🔊 语音文件: {result['audio_file']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()