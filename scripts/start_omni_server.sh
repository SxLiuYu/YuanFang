#!/bin/bash
# 启动 llama.cpp-omni server (MiniCPM-o 4.5 S2S)
LLAMA_SERVER="/Users/sxliuyu/llama.cpp-omni/build/bin/llama-server"
MODEL_DIR="/Users/sxliuyu/llama-models/MiniCPM-o-4_5-gguf"
PORT=8090

"$LLAMA_SERVER" \
  -m "$MODEL_DIR/MiniCPM-o-4_5-Q4_K_M.gguf" \
  --port "$PORT" \
  --host "0.0.0.0" \
  -ngl 99 \
  -c 4096 \
  --no-tts \
  -t 8 &
echo "llama-server PID: $!"