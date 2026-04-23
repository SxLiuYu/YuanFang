# Android 项目架构指南

## 目录结构规范

```
android/app/src/main/java/com/openclaw/homeassistant/
├── ui/                    # 表现层 - Activity 和 Fragment
│   ├── main/              # 主界面
│   ├── settings/          # 设置界面
│   ├── device/            # 设备管理界面
│   └── health/            # 健康档案界面
├── service/               # 业务层 - 后台服务和业务逻辑
│   ├── AIService.java
│   ├── SmartHomeService.java
│   ├── EnergyManagementService.java
│   └── ...
├── data/                  # 数据层 - 数据存储和访问
│   ├── local/             # 本地数据库
│   ├── remote/            # 远程 API
│   └── repository/        # 数据仓库
└── util/                  # 工具类 - 通用工具
    ├── SecureConfig.java
    ├── ThreadPoolManager.java
    └── ErrorHandler.java
```

## 分层职责

### 1. UI 层 (`ui/`)
- 负责 UI 展示和用户交互
- 包含 Activity、Fragment、Adapter
- 不包含业务逻辑，通过 Service 层调用

### 2. Service 层 (`service/`)
- 负责业务逻辑处理
- 处理网络请求、数据处理
- 通过 Callback 或 LiveData 返回结果

### 3. Data 层 (`data/`)
- 负责数据存储和访问
- 本地数据库 (Room/SQLite)
- 远程 API 调用
- 数据缓存

### 4. Util 层 (`util/`)
- 通用工具类
- 配置管理
- 错误处理
- 线程管理

## 编码规范

### 命名规范
- Activity: `XxxActivity.java`
- Service: `XxxService.java`
- Adapter: `XxxAdapter.java`
- ViewModel: `XxxViewModel.java`

### 包名规范
- UI 组件按功能模块分包
- Service 按业务领域分包
- 工具类统一放在 `util` 包

### 代码规范
1. 使用 `ThreadPoolManager` 管理后台任务，禁止直接 `new Thread()`
2. 使用 `ErrorHandler` 统一处理异常
3. 使用 `SecureConfig` 管理敏感配置
4. 日志使用 `Log` 类，禁止 `e.printStackTrace()`

## 新增文件规范

所有新增文件应按照以下规则放置：

| 文件类型 | 目标目录 |
|----------|----------|
| Activity | `ui/<功能模块>/` |
| Service | `service/` |
| Database/DAO | `data/local/` |
| API Client | `data/remote/` |
| 工具类 | `util/` |

## 渐进式迁移

现有代码采用渐进式迁移策略：
1. 新增文件按规范放置
2. 修改文件时顺便迁移
3. 每次版本迭代迁移部分模块

## 依赖关系

```
UI 层 → Service 层 → Data 层
       ↘    Util 层    ↙
```

- UI 层只能依赖 Service 层和 Util 层
- Service 层只能依赖 Data 层和 Util 层
- Data 层只能依赖 Util 层
- Util 层不依赖其他层