# 📱 多设备协同 - 阿里云部署指南

**版本**: v1.5 Multi-Device  
**后端**: 阿里云函数计算 + TableStore  
**状态**: ⏳ 待部署

---

## 🎯 架构说明

```
Android 设备 → 阿里云函数计算 (HTTP API) → TableStore
     ↓
  心跳上报 (1 分钟)
  设备注册
  状态查询
```

---

## 📋 部署步骤

### 步骤 1: 开通阿里云服务

1. **访问阿里云**
   ```
   https://www.aliyun.com/
   ```

2. **开通服务**
   - 函数计算 FC：https://fc.console.aliyun.com/
   - 表格存储 TableStore：https://ots.console.aliyun.com/

3. **创建 RAM 用户** (可选但推荐)
   - 访问：https://ram.console.aliyun.com/
   - 创建用户
   - 授予权限：
     - `AliyunOTSFullAccess`
     - `AliyunFCFullAccess`

---

### 步骤 2: 创建 TableStore 实例

1. **创建实例**
   ```
   1. 进入 TableStore 控制台
   2. 创建实例
      - 实例类型：性能型
      - 区域：cn-beijing (或离你最近的)
      - 名称：openclaw-devices
   ```

2. **创建数据表**
   ```
   1. 点击实例
   2. 创建表
      - 表名：devices
      - 主键：device_id (String)
      - 预留读 CU：1
      - 预留写 CU：1
   ```

3. **记录信息**
   ```
   - 实例名称：openclaw-devices
   - 实例地址：https://openclaw-devices.cn-beijing.ots.aliyuncs.com
   ```

---

### 步骤 3: 创建函数计算

1. **创建服务**
   ```
   1. 进入函数计算控制台
   2. 创建服务
      - 服务名：openclaw
      - 描述：OpenClaw 设备同步服务
   ```

2. **创建函数**
   ```
   1. 在服务中创建函数
   2. 选择"从零开始创建"
   3. 配置：
      - 函数名：device-sync
      - 运行环境：Python 3.9
      - 内存：512MB
      - 超时：60 秒
   ```

3. **上传代码**
   ```
   1. 打包代码:
      cd aliyun-function
      zip -r code.zip index.py requirements.txt
   
   2. 上传:
      - 代码上传：选择 code.zip
      - 依赖安装：自动
   ```

4. **配置触发器**
   ```
   1. 添加 HTTP 触发器
   2. 配置:
      - 请求方法：GET, POST, OPTIONS
      - 认证方式：匿名 (或函数计算签名)
   ```

5. **配置环境变量**
   ```
   ACCESS_KEY_ID=你的 AccessKey ID
   ACCESS_KEY_SECRET=你的 AccessKey Secret
   TABLESTORE_ENDPOINT=https://你的实例.cn-beijing.ots.aliyuncs.com
   TABLESTORE_INSTANCE_NAME=你的实例名
   TABLESTORE_TABLE_NAME=devices
   ```

---

### 步骤 4: 获取 API 地址

创建成功后，复制 HTTP 触发器 URL：
```
https://你的函数.fc.cn-beijing.aliyuncs.com/2016-08-15/proxy/openclaw/device-sync/
```

---

### 步骤 5: 配置 Android App

编辑 `DeviceSyncService.java`:
```java
private static final String API_BASE_URL = "https://你的函数.fc.cn-beijing.aliyuncs.com/2016-08-15/proxy/openclaw/device-sync/";
```

---

## 🧪 测试 API

### 1. 用户注册
```bash
curl -X POST "你的 URL/register_user" \
  -H "Content-Type: application/json" \
  -d '{"username": "laoyu"}'
```

**响应**:
```json
{
  "success": true,
  "user_id": "user_laoyu",
  "session_token": "mock_token"
}
```

### 2. 设备注册
```bash
curl -X POST "你的 URL/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test123",
    "device_name": "测试手机",
    "device_model": "Xiaomi 14",
    "user_id": "user_laoyu",
    "app_version": "1.5",
    "battery": 85
  }'
```

### 3. 心跳上报
```bash
curl -X POST "你的 URL/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test123",
    "battery": 80
  }'
```

### 4. 获取设备列表
```bash
curl -X GET "你的 URL/list?user_id=user_laoyu"
```

**响应**:
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "test123",
      "device_name": "测试手机",
      "device_model": "Xiaomi 14",
      "status": "online",
      "battery": 80,
      "last_seen_text": "刚刚"
    }
  ]
}
```

---

## 💰 成本估算

### 函数计算
- **免费额度**: 每月 100 万次调用
- **预计**: 100 台设备 × 1 次/分钟 × 60 分钟 × 24 小时 = 14.4 万次/天
- **费用**: 免费额度内 **0 元**

### TableStore
- **存储**: <1MB (几乎免费)
- **读/写 CU**: 按量付费
- **预计**: <1 元/月

**总计**: **约 1 元/月** (100 台设备以内)

---

## 📊 监控

### 函数计算监控
```
函数计算控制台 → 服务/函数 → 监控
- 调用次数
- 错误次数
- 平均耗时
```

### TableStore 监控
```
TableStore 控制台 → 实例 → 监控
- 读/写 QPS
- 存储量
- 流量
```

---

## 🔧 故障排查

### 问题 1: 函数调用失败
```
检查:
1. 环境变量是否正确
2. AccessKey 是否有效
3. TableStore 表是否存在
4. 函数日志 (控制台 → 日志)
```

### 问题 2: 设备列表为空
```
检查:
1. user_id 是否正确
2. 设备是否已注册
3. TableStore 中是否有数据
```

### 问题 3: 心跳未更新
```
检查:
1. 设备网络是否正常
2. 函数日志是否有错误
3. device_id 是否匹配
```

---

## 📁 文件清单

```
aliyun-function/
├── index.py              # 函数代码
├── requirements.txt      # Python 依赖
├── README.md            # 部署说明
└── code.zip             # 打包文件 (上传用)
```

---

## 🚀 下一步

1. ✅ 部署函数计算
2. ✅ 配置 Android App
3. ✅ 测试 API
4. ✅ GitHub Actions 编译 APK
5. ⏳ 用户测试

---

## 🔗 相关链接

- **函数计算文档**: https://help.aliyun.com/product/50980.html
- **TableStore 文档**: https://help.aliyun.com/product/29939.html
- **RAM 访问控制**: https://help.aliyun.com/product/28625.html

---

**开发者**: OpenClaw AI Assistant 🦞  
**状态**: ⏳ 待部署  
**预计成本**: ~1 元/月
