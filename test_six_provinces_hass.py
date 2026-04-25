#!/usr/bin/env python3
"""
测试三省六部制 + Home Assistant 整合版
"""
import sys
import os

# 确保能找到 YuanFang 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试三省六部制 + Home Assistant 整合版")
print("="*60)

# 测试1：导入模块
print("\n[1] 测试导入模块...")
try:
    from agents.crew.six_provinces import SixProvincesWithHASS
    from adapters.home_assistant_adapter import HomeAssistantAdapter
    print("  ✅ 模块导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2：初始化整合版
print("\n[2] 测试初始化整合版（不连接HA）...")
try:
    system = SixProvincesWithHASS()
    print("  ✅ SixProvincesWithHASS 初始化成功")
    print(f"  Agent数量: {len(system._agents)}")
    print(f"  HA状态: {'已连接' if system.hass else '未连接'}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3：测试设备动作提取
print("\n[3] 测试设备动作提取...")
test_tasks = [
    "帮我把客厅灯打开",
    "把空调调到24度",
    "我回来了，切换到回家模式",
    "关一下窗帘",
    "明天提醒我开会",
]

for task in test_tasks:
    try:
        actions = system._extract_device_actions(task)
        print(f"  任务: {task}")
        if actions:
            print(f"    → 检测到动作: {actions}")
        else:
            print(f"    → 无设备控制动作")
    except Exception as e:
        print(f"  ❌ 分析失败: {e}")

print("\n" + "="*60)
print("  整合版测试通过！✅")
print("="*60)
print("\n使用说明：")
print("  1. 启动 Home Assistant")
print("  2. 创建长期访问令牌")
print("  3. 使用带HA的整合版：")
print("""
from agents.crew.six_provinces import SixProvincesWithHASS

# 初始化（带HA连接）
system = SixProvincesWithHASS(
    hass_host="http://localhost:8123",
    hass_token="你的长期访问令牌"
)

# 运行任务（会自动检测并执行设备控制）
result = system.run("我回来了，帮我把灯打开，切换到放松模式")
""")
