#!/usr/bin/env python3
"""直接用本地路径加载MLX模型，避免网络请求"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🧪 直接加载本地MLX模型")
print("="*60)

# 1. 导入mlx_lm
print("\n1️⃣  导入mlx_lm...")
try:
    import mlx_lm
    from mlx_lm.utils import load_model, load_tokenizer
    print("✅ mlx_lm 导入成功！")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 用本地缓存路径（避免网络请求）
local_path = os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--gemma-4-E4B-it-4bit")
print(f"\n2️⃣  本地路径: {local_path}")

if not os.path.exists(local_path):
    print(f"❌ 路径不存在: {local_path}")
    # 试试其他可能的本地模型
    print("\n检查本地缓存的模型...")
    hub_dir = os.path.expanduser("~/.cache/huggingface/hub/")
    if os.path.exists(hub_dir):
        models = [d for d in os.listdir(hub_dir) if d.startswith("models--") and os.path.isdir(os.path.join(hub_dir, d))]
        print(f"找到 {len(models)} 个本地模型:")
        for m in models:
            print(f"  - {m}")
    sys.exit(1)

# 3. 直接用load_model和load_tokenizer，避免_download
print(f"\n3️⃣  加载模型和tokenizer...")
try:
    import mlx.core as mx
    from mlx_lm.models import gemma
    
    # 先加载配置
    import json
    config_path = os.path.join(local_path, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    print(f"✅ 配置加载成功: {config['model_type']}")
    
    # 加载tokenizer
    tokenizer = load_tokenizer(local_path)
    print("✅ Tokenizer加载成功！")
    
    # 加载模型
    model, _ = load_model(local_path)
    print("✅ 模型加载成功！")
    
    # 4. 测试生成
    prompt = "你好，请简单介绍一下自己（不超过50字）："
    print(f"\n4️⃣  测试生成，提示词: {prompt}")
    
    # 格式化消息（Gemma的chat template）
    messages = [{"role": "user", "content": prompt}]
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # 生成
    response = mlx_lm.generate(
        model=model,
        tokenizer=tokenizer,
        prompt=formatted_prompt,
        max_tokens=100,
        temp=0.7,
        verbose=True
    )
    
    print("\n✅ 成功！")
    print(f"\n💬 完整输出:\n{response}")
    
except Exception as e:
    print(f"\n❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 本地MLX模型测试完成！")
print("="*60)
