# 阿里云函数计算部署指南

## 步骤 1: 开通服务

1. 访问 https://fc.console.aliyun.com/
2. 开通函数计算服务
3. 开通 TableStore 服务

## 步骤 2: 创建 TableStore 实例

1. 访问 https://ots.console.aliyun.com/
2. 创建实例
   - 实例类型：性能型
   - 区域：选择离你最近的
3. 创建表
   - 表名：`devices`
   - 主键：`device_id` (String)

## 步骤 3: 获取 AccessKey

1. 访问 https://ram.console.aliyun.com/
2. 创建 RAM 用户
3. 授予权限：
   - `AliyunOTSFullAccess` (TableStore 完全访问权限)
   - `AliyunFCFullAccess` (函数计算完全访问权限)
4. 创建 AccessKey

## 步骤 4: 创建函数

1. 进入函数计算控制台
2. 创建服务：`openclaw`
3. 创建函数：
   - 运行环境：Python 3.9
   - 代码上传：上传 `index.py` 和 `requirements.txt`
   - 触发方式：HTTP 触发器
   - 请求方法：GET, POST, OPTIONS
   - 内存：512MB
   - 超时：60 秒

## 步骤 5: 配置环境变量

在函数配置中添加环境变量：
```
ACCESS_KEY_ID=你的 Key
ACCESS_KEY_SECRET=你的 Secret
TABLESTORE_ENDPOINT=https://你的实例.cn-beijing.ots.aliyuncs.com
TABLESTORE_INSTANCE_NAME=你的实例名
TABLESTORE_TABLE_NAME=devices
```

## 步骤 6: 获取 API 地址

创建成功后，复制 HTTP 触发器的 URL，格式：
```
https://你的函数.fc.cn-beijing.aliyuncs.com/2016-08-15/proxy/openclaw/你的函数/
```

## 步骤 7: 配置 Android App

编辑 `DeviceSyncService.java`，替换：
```java
private static final String API_BASE_URL = "你的函数 URL";
```

## 测试 API

### 设备注册
```bash
curl -X POST "你的 URL/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test123",
    "device_name": "测试设备",
    "device_model": "Xiaomi 14",
    "user_id": "user_001",
    "battery": 85
  }'
```

### 心跳上报
```bash
curl -X POST "你的 URL/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test123",
    "battery": 80
  }'
```

### 获取设备列表
```bash
curl -X GET "你的 URL/list?user_id=user_001"
```

## 成本估算

- 函数计算：免费额度内免费
- TableStore：按量付费，预计 <1 元/月

## 监控

- 函数计算控制台 → 监控
- TableStore 控制台 → 监控
