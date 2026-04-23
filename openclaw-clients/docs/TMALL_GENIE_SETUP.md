# 天猫精灵接入指南

## 📋 概述

天猫精灵（Tmall Genie）支持通过 IoT 开放平台接入第三方设备和应用。

---

## 🔑 第一步：申请 API 凭证

### 1. 注册天猫精灵开放平台账号

访问：https://open.tmall.com/

1. 使用淘宝/天猫账号登录
2. 进入「控制台」→「创建应用」
3. 选择「智能家居」类别
4. 填写应用信息（名称、描述等）

### 2. 获取 API Key 和 Secret

创建应用后，在应用详情页可以找到：
- **App Key** (API Key)
- **App Secret** (API Secret)

⚠️ **重要**：妥善保管 Secret，不要泄露！

---

## 🔗 第二步：配置设备接入

### 方式一：云云对接（推荐）

适合已有智能设备的用户，天猫精灵作为控制中心。

1. **登录天猫精灵 IoT 平台**
   - 访问：https://iot.taobao.com/
   
2. **添加设备品牌**
   - 创建品牌档案
   - 上传设备 SKU 信息

3. **配置设备能力**
   - 定义设备功能（开关、亮度、颜色等）
   - 映射到天猫精灵标准能力模型

4. **测试设备**
   - 使用天猫精灵 App 测试语音控制
   - 示例："天猫精灵，打开客厅灯"

### 方式二：自建技能

适合开发者自定义场景和对话逻辑。

1. **创建技能**
   - 访问：https://skill.aliyun.com/
   - 创建自定义技能

2. **配置意图**
   ```json
   {
     "intent": "ControlDevice",
     "slots": [
       {"name": "device_name", "type": "STRING"},
       {"name": "action", "type": "STRING"},
       {"name": "room", "type": "STRING"}
     ]
   }
   ```

3. **配置 Webhook**
   - 填写后端服务地址
   - 示例：`https://your-server.com/api/tmall/webhook`

---

## 💻 第三步：代码集成

### Android 配置

在 `SettingsActivity` 中添加天猫精灵配置入口：

```java
// 打开天猫精灵配置界面
private void setupTmallGenie() {
    new AlertDialog.Builder(this)
        .setTitle("配置天猫精灵")
        .setMessage("请输入天猫精灵 API Key 和 Secret")
        .setView(R.layout.dialog_tmall_config)
        .setPositiveButton("保存", (dialog, which) -> {
            String apiKey = apiKeyInput.getText().toString();
            String apiSecret = apiSecretInput.getText().toString();
            
            SmartHomeService.TmallGenieAdapter adapter = 
                (SmartHomeService.TmallGenieAdapter) smartHomeService.getAdapter("tmall");
            adapter.setCredentials(apiKey, apiSecret);
            
            // 从云端同步设备
            adapter.fetchDevicesFromCloud();
            
            Toast.makeText(this, "天猫精灵配置成功", Toast.LENGTH_SHORT).show();
        })
        .show();
}
```

### 后端 API 集成

在 `family_services_api.py` 中添加天猫精灵 Webhook：

```python
@app.route('/api/tmall/webhook', methods=['POST'])
def tmall_webhook():
    """天猫精灵语音控制 Webhook"""
    data = request.json
    
    # 解析语音指令
    intent = data.get('intent')
    slots = data.get('slots', {})
    
    device_name = slots.get('device_name')
    action = slots.get('action')
    
    # 查找设备并控制
    # ...
    
    return jsonify({
        'success': True,
        'response': f'已{action}{device_name}'
    })
```

---

## 🎯 支持的语音指令

配置完成后，可以使用以下语音指令：

### 基础控制
- "天猫精灵，打开客厅灯"
- "天猫精灵，关闭空调"
- "天猫精灵，把亮度调到 50%"
- "天猫精灵，设置温度为 26 度"

### 场景控制
- "天猫精灵，我回来了"（触发回家模式）
- "天猫精灵，我要睡觉了"（触发睡眠模式）
- "天猫精灵，我出门了"（触发离家模式）

### 查询类
- "天猫精灵，客厅温度是多少"
- "天猫精灵，还有哪些设备开着"

---

## 🔧 API 调用示例

### 控制设备

```bash
curl -X POST "https://openapi.tmall.com/router/rest" \
  -d "method=tmall.genie.ieq.device.control" \
  -d "app_key=YOUR_APP_KEY" \
  -d "device_id=DEVICE_ID" \
  -d "action=on" \
  -d "timestamp=$(date +%s)" \
  -d "sign=YOUR_SIGNATURE"
```

### 获取设备列表

```bash
curl -X POST "https://openapi.tmall.com/router/rest" \
  -d "method=tmall.genie.ieq.device.list" \
  -d "app_key=YOUR_APP_KEY" \
  -d "timestamp=$(date +%s)" \
  -d "sign=YOUR_SIGNATURE"
```

---

## 📱 在 App 中使用

### 添加天猫精灵设备

```java
// 添加天猫精灵设备
smartHomeService.addDevice(
    "001",           // 设备 ID
    "客厅灯",        // 设备名称
    "light",         // 设备类型
    "tmall",         // 平台：天猫精灵
    "客厅"           // 房间
);

// 控制设备
smartHomeService.controlDevice("TM_001", "on", null);
```

### 设备类型映射

| 天猫精灵类型 | 代码类型 | 支持动作 |
|-------------|---------|----------|
| 灯 (light) | light | on, off, set_brightness, set_color |
| 空调 (aircon) | aircon | on, off, set_temperature, set_mode |
| 插座 (outlet) | outlet | on, off |
| 窗帘 (curtain) | curtain | open, close, set_position |
| 电视 (tv) | tv | on, off, set_volume, set_channel |

---

## 🔐 签名算法

天猫精灵 API 请求需要签名，示例代码：

```java
public String generateSignature(Map<String, String> params, String secret) {
    // 1. 参数按字母排序
    List<String> keys = new ArrayList<>(params.keySet());
    Collections.sort(keys);
    
    // 2. 拼接参数字符串
    StringBuilder sb = new StringBuilder();
    for (String key : keys) {
        sb.append(key).append(params.get(key));
    }
    sb.append(secret);
    
    // 3. MD5 签名
    return MD5(sb.toString()).toUpperCase();
}
```

---

## 📚 参考文档

- **天猫精灵开放平台**: https://open.tmall.com/
- **IoT 平台文档**: https://iot.taobao.com/doc
- **API 参考**: https://open.tmall.com/doc/detail.htm?docId=22
- **技能开发**: https://skill.aliyun.com/

---

## 🐛 常见问题

### Q: 设备无法同步？
A: 检查 API Key/Secret 是否正确，确保设备已在天猫精灵 App 中绑定。

### Q: 语音控制无响应？
A: 检查 Webhook 地址是否可公网访问，服务器防火墙是否开放。

### Q: 签名验证失败？
A: 确保参数排序和签名算法与官方文档一致。

---

## 🎉 快速测试

配置完成后，运行以下命令测试：

```bash
# 1. 启动后端服务
python3 backend/services/family_services_api.py

# 2. 添加天猫精灵设备
curl -X POST http://localhost:8082/api/smarthome/device \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "TM_001",
    "device_name": "客厅灯",
    "device_type": "light",
    "platform": "tmall",
    "room": "客厅"
  }'

# 3. 控制设备
curl -X POST http://localhost:8082/api/smarthome/control \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "TM_001",
    "action": "on"
  }'
```

---

**配置完成后，你就可以用天猫精灵语音控制所有接入的设备了！** 🎊

[[reply_to_current]]
