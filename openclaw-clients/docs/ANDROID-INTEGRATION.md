# Android 客户端完整集成指南

## 架构总览

```
OpenClaw Home Assistant (Android)
│
├── OpenClawApplication          # 应用主类，管理所有服务
│   ├── DeviceAuthService        # 设备认证（飞书确认）
│   ├── TaskService              # 任务服务（拉取云端任务）
│   └── DeviceDataService        # 数据服务（上传设备数据）
│
├── MainActivity                 # 主界面（AI 对话 + 设备数据）
├── DeviceConfirmActivity        # 设备确认界面（输入飞书确认码）
└── NotificationHelper           # 通知管理
```

## 核心功能

### 1. 设备认证流程

```
首次启动
   ↓
DeviceAuthService.registerOrLogin()
   ↓
云端发送飞书确认消息
   ↓
显示 DeviceConfirmActivity
   ↓
用户输入 6 位确认码
   ↓
验证通过 → 保存永久令牌
   ↓
启动 TaskService + DeviceDataService
```

### 2. 任务拉取（每 5 分钟）

```
TaskService.start()
   ↓
GET /tasks/{device_id}
   ↓
收到任务 → 收集指定数据
   ↓
POST /device-data
   ↓
POST /task/complete
```

### 3. 数据上传（每 30 分钟）

```
DeviceDataService.start()
   ↓
收集电池、网络、步数等
   ↓
POST /device-data
   ↓
云端存储并检查告警
```

## 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `OpenClawApplication.java` | 应用主类，服务管理器 |
| `DeviceAuthService.java` | 设备认证服务 |
| `TaskService.java` | 任务拉取与执行 |
| `DeviceDataService.java` | 设备数据上传 |
| `DeviceConfirmActivity.java` | 设备确认界面 |
| `activity_device_confirm.xml` | 确认界面布局 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `AndroidManifest.xml` | 注册 Application、Activity、权限 |
| `MainActivity.java` | 添加认证检查 |
| `NotificationHelper.java` | 添加认证通知 |

## 集成步骤

### 1. 配置服务器地址

在以下文件中修改服务器地址：

**DeviceAuthService.java**
```java
private static final String SERVER_URL = "http://123.57.107.21:8081";
private static final String API_KEY = "openclaw_api_key_2026";
```

**TaskService.java**
```java
private static final String SERVER_URL = "http://123.57.107.21:8081";
private static final String API_KEY = "openclaw_api_key_2026";
```

**DeviceDataService.java**
```java
private static final String SERVER_URL = "http://123.57.107.21:8081";
private static final String API_KEY = "openclaw_api_key_2026";
```

### 2. 注册 Application

**AndroidManifest.xml**
```xml
<application
    android:name=".OpenClawApplication"
    ...>
```

### 3. 权限配置

确保有以下权限（已配置）：

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

### 4. 编译与测试

```bash
cd /home/admin/.openclaw/workspace/openclaw-clients/android
./gradlew assembleDebug
```

APK 输出位置：
```
app/build/outputs/apk/debug/app-debug.apk
```

## 使用流程

### 首次启动

1. **安装 App** → 打开
2. **自动注册设备** → 云端发送飞书确认消息
3. **收到通知** → 点击打开确认界面
4. **查看飞书** → 获取 6 位确认码
5. **输入确认码** → 点击"确认登录"
6. **认证成功** → 进入主界面

### 日常使用

- **AI 对话**：主界面直接对话
- **设备数据**：自动后台上传（每 30 分钟）
- **任务执行**：自动拉取并执行（每 5 分钟）
- **查看状态**：设置 → 设备管理

## 服务管理

### 查看服务状态

```java
OpenClawApplication app = OpenClawApplication.getInstance();

// 认证状态
boolean confirmed = app.isDeviceConfirmed();

// 令牌
String token = app.getDeviceToken();

// 服务实例
DeviceAuthService authService = app.getAuthService();
TaskService taskService = app.getTaskService();
DeviceDataService deviceDataService = app.getDeviceDataService();
```

### 手动控制

```java
// 重新认证
app.reAuthenticate();

// 退出登录
app.logout();

// 停止服务
taskService.stop();
deviceDataService.stop();
```

## 通知类型

| 通知类型 | 触发条件 | 操作 |
|---------|---------|------|
| 设备认证 | 首次启动/重新认证 | 点击打开确认界面 |
| 新任务 | 云端下发新任务 | 点击查看任务详情 |
| 任务完成 | 任务执行完成 | 查看完成结果 |

## 数据存储

### SharedPreferences

**device_auth**
- `device_id` - 设备唯一 ID
- `device_token` - 认证令牌
- `device_confirmed` - 是否已确认
- `device_name` - 设备名称

**task_service**
- `last_upload` - 最后上传时间

**device_data**
- `last_fetch` - 最后拉取任务时间

### 本地文件

```
/data/data/com.openclaw.homeassistant/shared_prefs/
├── device_auth.xml
├── task_service.xml
└── device_data.xml
```

## 云端 API

### 认证相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/device/register` | POST | 设备注册/登录 |
| `/device/confirm` | POST | 确认码验证 |

### 任务相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/tasks/{device_id}` | GET | 拉取任务 |
| `/task/complete` | POST | 标记完成 |

### 数据相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/device-data` | POST | 上传数据 |
| `/device-data/{device_id}` | GET | 查询数据 |

## 调试技巧

### 1. 查看日志

```bash
adb logcat | grep -E "OpenClaw|DeviceAuth|TaskService|DeviceData"
```

### 2. 清除数据重新认证

```bash
adb shell pm clear com.openclaw.homeassistant
```

### 3. 查看 SharedPreferences

```bash
adb shell
cd /data/data/com.openclaw.homeassistant/shared_prefs
cat device_auth.xml
```

### 4. 模拟服务器响应

修改 `SERVER_URL` 指向本地测试服务器：
```java
private static final String SERVER_URL = "http://10.0.2.2:8081";  // Android 模拟器访问本机
```

## 常见问题

### Q: 收不到飞书确认消息？
A: 检查服务器日志，确认飞书 App ID 和 Secret 配置正确。

### Q: 确认码输入后提示错误？
A: 确认码区分大小写，确保转换为大写。

### Q: 服务不启动？
A: 检查 `OpenClawApplication` 是否正确注册，查看日志是否有异常。

### Q: 数据上传失败？
A: 检查网络连接，确认设备已认证成功，令牌有效。

## 下一步优化

1. **计步器集成** - 接入 Google Fit/华为运动健康
2. **位置采集** - 添加 GPS 定位权限和数据上传
3. **应用列表** - 获取已安装应用信息
4. **截屏功能** - 远程截屏（需要无障碍权限）
5. **推送通知** - 集成 Firebase/华为推送

---

**编译命令：**
```bash
cd /home/admin/.openclaw/workspace/openclaw-clients/android
./gradlew clean assembleDebug
```

**APK 位置：**
```
app/build/outputs/apk/debug/app-debug.apk
```

**安装到设备：**
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```
