#!/usr/bin/env python3
"""直接测试本地MLX模型"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🧪 测试本地MLX模型")
print("="*60)

# 1. 导入mlx_lm
print("\n1️⃣  导入mlx_lm...")
try:
    import mlx_lm
    print("✅ mlx_lm 导入成功！")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试模型（用Qwen3-8B-4bit，这个是标准模型）
model_name = "mlx-community/Qwen3-8B-4bit"
print(f"\n2️⃣  加载模型: {model_name}...")

try:
    # 正确使用mlx_lm的API：先load，再generate
    print("   (第一次运行会比较慢，因为要加载模型...)")
    
    model, tokenizer = mlx_lm.load(model_name)
    
    print("✅ 模型加载成功！")
    
    prompt = "你好，请简单介绍一下自己（不超过50字）："
    
    print(f"\n3️⃣  生成回复，提示词: {prompt}")
    
    # 生成
    response = mlx_lm.generate(
        model=model,
        tokenizer=tokenizer,
        prompt=prompt,
        max_tokens=100,
        temp=0.7,
        verbose=True
    )
    
    print("\n✅ 成功！")
    print(f"\n💬 完整输出:\n{response}")
    
    # 尝试提取回答部分
    if response.startswith(prompt):
        answer = response[len(prompt):].strip()
        print(f"\n💡 纯回答:\n{answer}")
    
except Exception as e:
    print(f"\n❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 MLX本地模型测试完成！")
print("="*60)
