# Environment Report Skill

**Category:** conversation  
**When to Use:** When the user asks about current home environment (temperature, humidity, air quality, device status).

## Trigger Patterns
- 环境怎么样
- 家里什么情况
- 温湿度
- 空气质量
- 当前温度
- 屋里热不热

## Steps

1. **查询 KAIROS 工具获取环境数据**
   ```python
   from services.kairos_tools import get_kairos_tools
   tools = get_kairos_tools()
   env = tools.sense_environment(nodes_data)
   ```

2. **格式化回复**
   - 温度：数值 + 舒适度评价
   - 湿度：数值 + 评价
   - 空气质量：AQI + 等级

3. **给出建议**（如果需要）
   - 温度>28°C：建议开空调
   - 湿度>70%：建议开除湿
   - AQI>100：建议开新风

## Output Format
```
当前环境：
🌡️ 温度：26°C（舒适）
💧 湿度：55%（适宜）
🌬️ 空气质量：优（AQI 42）
```
