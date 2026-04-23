# OpenClaw Clients 开发者文档

**面向开发者的高级配置和 API 文档**

---

## 🏗️ 架构设计

### 系统架构
```
┌─────────────────────────────────────┐
│         用户界面层 (7 平台)          │
│  Android/iOS/Web/Flutter/音箱/...   │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│       业务逻辑层 (Android Service)   │
│  SmartHome/Finance/Task/Shopping    │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│        后端服务层 (Python Flask)     │
│   REST API + AI 技能 + 数据同步      │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│         数据存储层                    │
│   SQLite + 阿里云 OSS + 本地文件     │
└─────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **Android** | Java + Material Design + MPAndroidChart |
| **后端** | Python 3.9 + Flask + SQLite |
| **AI** | 通义千问 (DashScope) |
| **IoT** | 米家/涂鸦/天猫精灵 API |
| **部署** | GitHub Actions + 阿里云 OSS |

---

## 📁 项目结构

```
openclaw-clients/
├── android/                      # Android 原生客户端
│   └── app/src/main/java/.../
│       ├── SmartHomeService.java    # 智能家居服务
│       ├── FinanceService.java      # 家庭账本服务
│       ├── TaskService.java         # 任务板服务
│       ├── ShoppingService.java     # 购物清单服务
│       ├── MemberService.java       # 成员管理服务
│       ├── ChartService.java        # 图表服务
│       └── ...
│
├── backend/services/             # 后端服务
│   ├── family_services_api.py       # REST API
│   ├── tmall_ai_skill.py            # 天猫精灵技能
│   ├── smart_home_integration.py    # 智能家居集成
│   ├── price_crawler.py             # 价格爬取
│   ├── chart_generator.py           # 图表生成
│   ├── smart_reminder_service.py    # 智能提醒
│   ├── automation_engine.py         # 自动化引擎
│   ├── device_data_service.py       # 设备数据
│   ├── cloud_sync_service.py        # 云同步
│   └── smart_recommendation_service.py # 智能推荐
│
├── docs/                         # 文档
│   ├── USER_GUIDE.md                # 使用文档
│   ├── QUICK_START.md               # 快速开始
│   ├── DEVELOPER_GUIDE.md           # 开发者文档（本文件）
│   └── ...
│
└── .github/workflows/            # CI/CD
    ├── android-ci.yml               # Android CI
    └── release-apk.yml              # APK 发布
```

---

## 🔧 开发环境搭建

### 1. Android 开发环境

```bash
# 安装 Android Studio
# https://developer.android.com/studio

# 克隆项目
git clone https://github.com/SxLiuYu/openclaw-clients.git

# 打开项目
cd android
# 在 Android Studio 中打开
```

### 2. 后端开发环境

```bash
# Python 3.9+
cd backend/services

# 安装依赖
pip3 install -r requirements.txt

# 启动服务
python3 family_services_api.py
```

### 3. 测试环境

```bash
# Android 测试
cd android
./gradlew test

# Python 测试
cd backend/services
pytest test_family_services_api.py -v
```

---

## 🔌 API 开发指南

### RESTful API 规范

**基础 URL**: `http://localhost:8082`

**请求格式**: JSON
**响应格式**: JSON

### API 示例

#### 添加设备
```python
@app.route('/api/smarthome/device', methods=['POST'])
def add_device():
    data = request.json
    device_id = data['device_id']
    device_name = data['device_name']
    
    # 保存到数据库
    # ...
    
    return jsonify({'success': True})
```

#### 控制设备
```python
@app.route('/api/smarthome/control', methods=['POST'])
def control_device():
    data = request.json
    device_id = data['device_id']
    action = data['action']
    value = data.get('value')
    
    # 调用平台 API
    if device_id.startswith('MI_'):
        mihome_control(device_id, action, value)
    elif device_id.startswith('TY_'):
        tuya_control(device_id, action, value)
    
    return jsonify({'success': True})
```

---

## 🤖 AI 技能开发

### 天猫精灵技能配置

#### 1. 创建技能
访问：https://skill.aliyun.com/

#### 2. 配置意图
```json
{
  "intent_name": "AIChat",
  "samples": [
    "今天花了多少钱",
    "有哪些待办任务"
  ]
}
```

#### 3. 配置 Webhook
```
URL: https://your-server.com/api/tmall/webhook
Method: POST
```

#### 4. 实现处理逻辑
```python
@app.route('/api/tmall/webhook', methods=['POST'])
def tmall_webhook():
    data = request.json
    intent = data.get('intent', {})
    query = data.get('query', '')
    
    # 调用通义千问
    response = call_dashscope(query)
    
    return jsonify({
        'response': {
            'prompts': [{'content': response}]
        }
    })
```

---

## 📊 数据库设计

### 核心表结构

#### 设备表 (smart_devices)
```sql
CREATE TABLE smart_devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    device_name TEXT,
    device_type TEXT,
    platform TEXT,
    room TEXT,
    is_online BOOLEAN
);
```

#### 交易表 (transactions)
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    amount REAL,
    type TEXT,
    category TEXT,
    recorded_by TEXT,
    recorded_at TIMESTAMP
);
```

#### 任务表 (tasks)
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    task_name TEXT,
    assigned_to TEXT,
    points INTEGER,
    status TEXT,
    due_date TIMESTAMP
);
```

---

## 🧪 测试指南

### Android 单元测试

```java
@RunWith(RobolectricTestRunner.class)
public class FinanceServiceTest {
    
    @Test
    public void testAddTransaction() {
        financeService.addTransaction(50.0, "expense", "餐饮", null, null, "测试");
        assertNotNull(financeService);
    }
}
```

### Python API 测试

```python
def test_add_transaction():
    response = client.post('/api/finance/transaction', json={
        'amount': 50.0,
        'type': 'expense',
        'category': '餐饮'
    })
    assert response.status_code == 200
```

---

## 🚀 部署指南

### 1. Android APK 发布

```bash
# 构建 Release APK
cd android
./gradlew assembleRelease

# APK 位置
android/app/build/outputs/apk/release/app-release.apk
```

### 2. 后端服务部署

#### 阿里云函数计算
```yaml
# template.yml
ROSTemplateFormatVersion: '2015-09-01'
Resources:
  FamilyService:
    Type: Aliyun::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: python3.9
      CodeUri: ./backend
```

#### Docker 部署
```dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["python3", "family_services_api.py"]
```

### 3. CI/CD 配置

GitHub Actions 自动构建和发布：
- 每次 push 触发 Android CI
- 打标签自动发布 Release APK

---

## 🔐 安全指南

### API Key 管理
```java
// 使用 EncryptedSharedPreferences
EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV
)
```

### 数据加密
```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# 加密
encrypted = cipher.encrypt(b"sensitive_data")

# 解密
decrypted = cipher.decrypt(encrypted)
```

---

## 📝 贡献指南

### 提交代码
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- Android: 遵循 [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- Python: 遵循 [PEP 8](https://pep8.org/)

---

## 📞 技术支持

- **GitHub**: https://github.com/SxLiuYu/openclaw-clients
- **Issues**: https://github.com/SxLiuYu/openclaw-clients/issues
- **邮箱**: 通过 GitHub Issues 联系

---

**祝开发愉快！** 🎉

[[reply_to_current]]
