# 设备登录认证系统文档

## 一、需求背景

### 1.1 问题描述

OpenClaw 多端客户端（Windows、Android）需要安全的设备认证机制，确保只有用户授权的设备才能访问系统。

### 1.2 业务需求

1. **设备注册**：新设备首次启动时需要注册
2. **安全确认**：通过飞书机器人发送确认码，用户输入后完成认证
3. **持久化令牌**：认证成功后保存令牌，后续启动无需再次确认
4. **多设备管理**：支持查看已认证设备列表

---

## 二、系统架构

### 2.1 整体流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Windows 客户端 │     │    后端 API     │     │   飞书机器人    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. POST /device/register                      │
         │  {device_id, device_name}                      │
         │──────────────────────>│                       │
         │                       │                       │
         │                       │  2. 生成确认码        │
         │                       │  发送飞书消息         │
         │                       │──────────────────────>│
         │                       │                       │
         │  3. 返回 {temp_id, status: "pending"}          │
         │<──────────────────────│                       │
         │                       │                       │
         │  4. 用户输入确认码    │                       │
         │                       │                       │
         │  5. POST /device/confirm                       │
         │  {temp_id, confirm_code}                       │
         │──────────────────────>│                       │
         │                       │                       │
         │  6. 验证确认码        │                       │
         │  生成永久令牌         │                       │
         │                       │                       │
         │  7. 返回 {confirmed: true, token: "xxx"}       │
         │<──────────────────────│                       │
         │                       │                       │
         │  8. 保存令牌到本地    │                       │
         │                       │                       │
```

### 2.2 组件说明

| 组件 | 文件 | 职责 |
|------|------|------|
| **后端认证服务** | `backend/services/device_auth_service.py` | 设备注册、确认码生成、令牌管理、飞书通知 |
| **Windows 认证服务** | `windows-desktop/.../DeviceAuthService.cs` | HTTP 请求、令牌存储、状态管理 |
| **确认码界面** | `windows-desktop/.../DeviceConfirmWindow.xaml` | 用户输入确认码的 UI |

---

## 三、API 设计

### 3.1 设备注册

**请求**
```
POST /device/register
Content-Type: application/json

{
    "device_id": "abc123...",
    "device_name": "DESKTOP-PC",
    "device_model": "Windows 11"
}
```

**响应 - 已确认**
```json
{
    "success": true,
    "confirmed": true,
    "token": "permanent_token_xxx",
    "device_name": "DESKTOP-PC"
}
```

**响应 - 待确认**
```json
{
    "success": true,
    "confirmed": false,
    "status": "pending",
    "temp_id": "temp_xxx",
    "message": "请查看飞书获取确认码"
}
```

### 3.2 设备确认

**请求**
```
POST /device/confirm
Content-Type: application/json

{
    "temp_id": "temp_xxx",
    "confirm_code": "ABC123"
}
```

**响应 - 成功**
```json
{
    "success": true,
    "confirmed": true,
    "token": "permanent_token_xxx",
    "device_name": "DESKTOP-PC",
    "message": "设备登录成功"
}
```

**响应 - 失败**
```json
{
    "success": false,
    "confirmed": false,
    "message": "确认码错误，请重新输入"
}
```

### 3.3 检查设备状态

**请求**
```
GET /device/status?device_id=abc123...
```

**响应**
```json
{
    "success": true,
    "confirmed": true,
    "device_name": "DESKTOP-PC",
    "last_seen": "2026-03-23T10:30:00"
}
```

### 3.4 设备登出

**请求**
```
POST /device/logout
Content-Type: application/json

{
    "device_id": "abc123..."
}
```

---

## 四、数据模型

### 4.1 后端数据结构

```python
@dataclass
class PendingConfirmation:
    """待确认的设备"""
    device_id: str
    device_name: str
    device_model: str
    confirm_code: str          # 6位确认码
    temp_id: str               # 临时ID
    created_at: datetime
    expires_at: datetime       # 5分钟有效期

@dataclass
class ConfirmedDevice:
    """已确认的设备"""
    device_id: str
    device_name: str
    device_model: str
    token: str                 # 永久令牌
    confirmed_at: datetime
    last_seen: datetime
```

### 4.2 Windows 客户端数据结构

```csharp
public class DeviceInfo
{
    public string DeviceId { get; set; }
    public string DeviceName { get; set; }
    public string DeviceModel { get; set; }
    public string Token { get; set; }
    public bool IsConfirmed { get; set; }
    public DateTime ConfirmedAt { get; set; }
}

public class DeviceAuthResult
{
    public bool Success { get; set; }
    public bool Confirmed { get; set; }
    public string? Token { get; set; }
    public string? Status { get; set; }
    public string? TempId { get; set; }
    public string? Message { get; set; }
}
```

---

## 五、核心代码逻辑

### 5.1 后端：确认码生成

```python
def generate_confirm_code(self) -> str:
    """生成 6 位确认码（避免易混淆字符）"""
    return ''.join(secrets.choice(
        'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    ) for _ in range(6))
```

### 5.2 后端：飞书通知

```python
def _send_feishu_notification(self, device_name: str, confirm_code: str):
    message = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🔐 设备登录确认"},
                "template": "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", 
                 "content": f"**设备名称：**{device_name}"}},
                {"tag": "div", "text": {"tag": "lark_md", 
                 "content": f"**确认码：**`{confirm_code}`"}},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": "⏱️ 确认码有效期：5 分钟"}
                ]}
            ]
        }
    }
    requests.post(self.feishu_webhook, json=message)
```

### 5.3 Windows：设备注册

```csharp
public async Task<DeviceAuthResult> RegisterOrLoginAsync()
{
    var requestData = new
    {
        device_id = DeviceId,
        device_name = Environment.MachineName,
        device_model = $"Windows {Environment.OSVersion.Version.Major}"
    };
    
    var response = await _httpClient.PostAsync(
        $"{_serverUrl}/device/register",
        new StringContent(JsonConvert.SerializeObject(requestData))
    );
    
    var result = JsonConvert.DeserializeObject<DeviceAuthResult>(
        await response.Content.ReadAsStringAsync());
    
    if (result.Confirmed)
    {
        SaveDeviceInfo();  // 保存令牌到本地
    }
    
    return result;
}
```

### 5.4 Windows：启动流程

```csharp
protected override void OnStartup(StartupEventArgs e)
{
    // 初始化服务
    var deviceAuth = ServiceProvider.GetRequiredService<DeviceAuthService>();
    
    // 检查认证状态
    if (!deviceAuth.IsConfirmed)
    {
        // 显示确认码输入窗口
        var confirmWindow = new DeviceConfirmWindow(deviceAuth);
        if (confirmWindow.ShowDialog() != true)
        {
            Shutdown();  // 用户取消，退出应用
            return;
        }
    }
    
    // 显示主窗口
    var mainWindow = ServiceProvider.GetRequiredService<MainWindow>();
    mainWindow.Show();
}
```

---

## 六、安全机制

### 6.1 确认码安全

- **字符集**：使用 `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`，避免 `0/O`, `1/I/L` 等易混淆字符
- **有效期**：5 分钟后自动过期
- **一次性**：确认成功后立即删除临时记录

### 6.2 令牌安全

- **长度**：32 字节的 URL-safe Base64 编码
- **唯一性**：使用 `secrets.token_urlsafe()` 生成
- **存储**：保存在用户 AppData 目录，权限受限

### 6.3 传输安全

- 生产环境建议使用 HTTPS
- 令牌在请求头中传递：`Authorization: Bearer {token}`

---

## 七、配置说明

### 7.1 后端配置

```python
# 飞书 Webhook URL
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

# 确认码有效期（分钟）
CONFIRMATION_EXPIRY_MINUTES = 5

# 确认码长度
CONFIRMATION_CODE_LENGTH = 6
```

### 7.2 Windows 客户端配置

```csharp
// 服务器地址
var serverUrl = "http://localhost:8000";

// 配置文件路径
var configPath = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
    "OpenClaw",
    "device_auth.json"
);
```

---

## 八、使用示例

### 8.1 首次启动

1. 用户启动 Windows 客户端
2. 客户端检测到未认证，显示确认窗口
3. 后端生成确认码 `XM7K9P`，发送到飞书
4. 用户在飞书查看确认码，输入到客户端
5. 认证成功，保存令牌

### 8.2 后续启动

1. 客户端检测到已认证
2. 直接显示主窗口，无需再次确认

### 8.3 设备登出

用户可在设置页面点击"退出登录"，清除本地令牌，下次启动需要重新认证。

---

## 九、扩展计划

### 9.1 短期

- [ ] 添加设备管理页面（查看已认证设备列表）
- [ ] 支持远程登出设备
- [ ] 添加设备别名功能

### 9.2 中期

- [ ] 支持多用户切换
- [ ] 添加设备在线状态检测
- [ ] 支持二维码扫描确认

### 9.3 长期

- [ ] 集成企业微信、钉钉通知
- [ ] 支持 FIDO2 硬件密钥
- [ ] 添加生物识别二次验证

---

## 十、文件清单

| 文件 | 类型 | 描述 |
|------|------|------|
| `backend/services/device_auth_service.py` | Python | 后端认证服务 |
| `windows-desktop/.../DeviceAuthService.cs` | C# | Windows 认证服务 |
| `windows-desktop/.../DeviceConfirmWindow.xaml` | XAML | 确认码输入界面 |
| `windows-desktop/.../DeviceConfirmWindow.xaml.cs` | C# | 界面代码后置 |
| `windows-desktop/.../DeviceConfirmViewModel.cs` | C# | 界面逻辑 |
| `windows-desktop/.../DeviceAuth.cs` | C# | 数据模型 |

---

## 十一、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-23 | 初始版本，支持设备注册和确认码认证 |