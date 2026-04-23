# Home Control Skill

**Category:** ha_control  
**When to Use:** When the user wants to control smart home devices (lights, switches, climate, scenes).

## Trigger Patterns
- 打开/关闭 [设备]
- 开灯/关灯/开空调
- 晚安模式/早安模式
- 离家模式/回家模式
- 全屋关灯

## Steps

1. **识别设备类型和动作**
   - 灯光类：开/关 → turn_on / turn_off
   - 场景类：晚安/早安/离家/回家 → activate_scene
   - 空词类：调温度/设温度 → set_value / select_option

2. **生成 HA 命令**
   ```python
   commands = [
       {"entity_id": f"switch.{device}", "action": "turn_on"},
   ]
   ```

3. **执行并反馈**
   - 执行成功后用中文描述结果
   - 失败时说明原因并提供建议

## Output Format
执行结果 + 当前设备状态摘要

## References
- `references/home_control.py` — YuanFang HA command builder
