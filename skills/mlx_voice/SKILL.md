# MLX Voice 触手

**Category:** mlx_voice  
**When to Use:** When the user wants to use the local Mac Mini M4 MLX pipeline for voice interaction (speech-to-text → LLM → text-to-speech).

## Trigger Patterns
- 语音模式
- 本地模型
- MLX 语音
- 用本地模型聊天
- 离线语音

## Steps

1. **检查依赖**
   - OMLX Server: `http://localhost:8080` (Gemma 4B 4bit)
   - Whisper STT: `mlx_whisper` (需安装)
   - Kokoro TTS: `mlx_audio` + `prince-canuma/Kokoro-82M` (需安装)

2. **语音转文字**
   ```python
   import mlx_whisper
   text = mlx_whisper.transcribe(audio_file)["text"]
   ```

3. **LLM 推理** (通过 OMLX Server)
   ```python
   # POST http://localhost:8080/v1/chat/completions
   response = omlx.chat(text)
   ```

4. **文字转语音**
   ```python
   from mlx_audio.tts.generate import generate_audio
   generate_audio(text=response, voice="af_heart")
   ```

## Output Format
执行结果 + 生成语音文件路径

## Dependencies
```bash
# 安装依赖（可选）
~/.venv-omlx/bin/pip install mlx-whisper mlx-audio
```

## References
- `references/mlx_voice.py` — 完整 MLX 语音管线实现
- OMLX Server: `http://localhost:8080`
- 模型路径: `~/omlx-models/gemma-4-E4B-it-4bit/`