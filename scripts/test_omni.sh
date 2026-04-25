#!/bin/bash
# 测试 llama-omni-cli 文字推理
LLAMA_CLI="/Users/sxliuyu/llama.cpp-omni/build/bin/llama-omni-cli"
MODEL_DIR="/Users/sxliuyu/llama-models/MiniCPM-o-4_5-gguf"

"$LLAMA_CLI" \
  -m "$MODEL_DIR/MiniCPM-o-4_5-Q4_K_M.gguf" \
  --no-tts \
  -c 2048 \
  -ngl 99 \
  -p "你好，介绍一下自己" \
  -n 50