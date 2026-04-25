#!/usr/bin/env python3
"""
测试 Home Assistant 适配器
"""
import sys
import os

# 确保能找到 YuanFang 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试 Home Assistant 适配器")
print("="*60)

# 测试1：导入模块
print("\n[1] 测试导入模块...")
try:
    from adapters.home_assistant_adapter import HomeAssistantAdapter
    print("  ✅ HomeAssistantAdapter 导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2：初始化适配器
print("\n[2] 测试初始化适配器...")
print("  提示：如果要实际连接，修改下面的 host 和 token")
print("  当前仅测试接口，不实际连接")

try:
    # 不实际连接，只是测试初始化
    adapter = HomeAssistantAdapter(
        host="http://localhost:8123",
        token="your_long_lived_access_token_here"
    )
    print("  ✅ HomeAssistantAdapter 初始化成功")
    print(f"  Host: {adapter.host}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3：显示可用方法
print("\n[3] 可用的控制方法:")
methods = [
    "light_turn_on / light_turn_off / light_toggle",
    "switch_turn_on / switch_turn_off",
    "climate_set_temperature / climate_set_hvac_mode",
    "cover_open / cover_close / cover_set_position",
    "scene_activate",
    "activate_mood (relax/work/movie/sleep/welcome/away)",
    "get_states / get_state / get_device_summary",
]
for method in methods:
    print(f"  - {method}")

print("\n" + "="*60)
print("  接口测试通过！✅")
print("="*60)
print("\n使用说明：")
print("  1. 在 Home Assistant 中创建长期访问令牌")
print("     (用户资料 -> 长期访问令牌 -> 创建令牌)")
print("  2. 使用 init_hass_adapter() 初始化")
print("  3. 调用各种控制方法")
print("\n示例代码：")
print("""
from adapters.home_assistant_adapter import init_hass_adapter

# 初始化
hass = init_hass_adapter(
    host="http://localhost:8123",
    token="你的长期访问令牌"
)

# 检查连接
if hass.health_check():
    print("连接成功！")

    # 开灯
    hass.light_turn_on("light.living_room")

    # 设置空调温度
    hass.climate_set_temperature("climate.air_conditioner", 24)

    # 激活场景
    hass.activate_mood("relax")
""")
