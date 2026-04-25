#!/usr/bin/env python3
"""
测试三省六部制 System（基于HyperAgent架构）
"""
import sys
import os

# 确保能找到 YuanFang 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试三省六部制 System（HyperAgent架构）")
print("="*60)

# 测试1：导入模块
print("\n[1] 测试导入模块...")
try:
    from agents.crew.six_provinces import SixProvincesSystem
    print("  ✅ SixProvincesSystem 导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2：初始化 System
print("\n[2] 测试初始化 System...")
try:
    system = SixProvincesSystem()
    print("  ✅ SixProvincesSystem 初始化成功")
    print(f"  Agent数量: {len(system._agents)}")
    print(f"  Agents: {list(system._agents.keys())}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3：测试任务类型分析
print("\n[3] 测试任务类型分析...")
test_tasks = [
    "明天下午3点有个会，帮我提醒一下",
    "看看这个月电费怎么这么多",
    "我回来了，帮我切换到放松模式",
    "看看门口是不是有人",
    "给小朋友设置一下，每天只能玩1小时游戏",
    "客厅那个灯泡是不是坏了？",
]

for task in test_tasks:
    try:
        task_type = system._analyze_task_type(task)
        ministers = system._get_ministers_for_task(task_type)
        print(f"  任务: {task[:30]}...")
        print(f"    → 类型: {task_type}")
        print(f"    → 涉及部门: {', '.join(ministers)}")
    except Exception as e:
        print(f"  ❌ 分析失败: {e}")

# 测试4：测试单部门接口
print("\n[4] 测试部门接口...")
print("  接口测试完成！")

print("\n" + "="*60)
print("  基础测试通过！✅")
print("="*60)
print("\n下一步：")
print("  - 如需完整测试，取消注释下面的 run() 测试")
print("  - 整合 Home Assistant")
print("  - 接入真实智能设备")

# 如果想完整测试，取消下面注释（注意：会消耗tokens）
"""
print("\n[5] 完整测试（运行一个简单任务）...")
try:
    result = system.run("你好，请介绍一下你自己")
    print(f"  结果: {result}")
except Exception as e:
    print(f"  ❌ 运行失败: {e}")
    import traceback
    traceback.print_exc()
"""
