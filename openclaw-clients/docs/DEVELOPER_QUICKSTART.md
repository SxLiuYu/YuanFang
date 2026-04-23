# 新功能快速开始指南

## 📦 已添加文件

### Android 核心服务
- `SmartHomeService.java` - 智能家居统一控制
- `FinanceService.java` - 家庭账本
- `TaskService.java` - 家庭任务板
- `ShoppingService.java` - 智能购物清单

### 后端 API
- `backend/services/family_services_api.py` - Flask 后端服务

### UI 布局
- `activity_smart_home.xml` - 智能家居界面
- `activity_finance.xml` - 家庭账本界面
- `activity_family_tasks.xml` - 任务板界面
- `activity_shopping_list.xml` - 购物清单界面

### 文档
- `docs/FEATURE_PROPOSAL.md` - 详细功能提案

---

## 🚀 快速启动

### 1. 启动后端服务

```bash
cd /home/admin/.openclaw/workspace/openclaw-clients/backend/services

# 安装依赖
pip3 install flask flask-cors

# 启动服务
python3 family_services_api.py
```

后端服务将在 `http://localhost:8082` 运行

### 2. Android 集成

#### 在 AndroidManifest.xml 添加 Activity

```xml
<activity android:name=".SmartHomeActivity" />
<activity android:name=".FinanceActivity" />
<activity android:name=".FamilyTasksActivity" />
<activity android:name=".ShoppingListActivity" />
```

#### 创建 Activity 类（示例：SmartHomeActivity）

```java
package com.openclaw.homeassistant;

import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class SmartHomeActivity extends AppCompatActivity 
    implements SmartHomeService.DeviceListener {
    
    private SmartHomeService smartHomeService;
    private RecyclerView recyclerDevices;
    private TextView txtEnergyStats;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_smart_home);
        
        smartHomeService = new SmartHomeService(this);
        SmartHomeService.setListener(this);
        
        recyclerDevices = findViewById(R.id.recycler_devices);
        txtEnergyStats = findViewById(R.id.txt_energy_stats);
        
        // 设置场景按钮
        findViewById(R.id.btn_home_mode).setOnClickListener(v -> 
            smartHomeService.executeScene("home_mode"));
        findViewById(R.id.btn_away_mode).setOnClickListener(v -> 
            smartHomeService.executeScene("away_mode"));
        findViewById(R.id.btn_sleep_mode).setOnClickListener(v -> 
            smartHomeService.executeScene("sleep_mode"));
        
        // 加载设备列表
        loadDevices();
    }
    
    private void loadDevices() {
        List<SmartHomeService.DeviceInfo> devices = smartHomeService.getAllDevices();
        // 设置 RecyclerView 适配器
        recyclerDevices.setLayoutManager(new LinearLayoutManager(this));
        // recyclerDevices.setAdapter(new DeviceAdapter(devices));
    }
    
    @Override
    public void onDeviceStatusChanged(String deviceId, boolean isOnline) {
        runOnUiThread(() -> {
            // 更新设备状态
        });
    }
    
    @Override
    public void onSceneActivated(String sceneId, String sceneName) {
        runOnUiThread(() -> {
            NotificationHelper.sendHealthNotification(this, 
                "场景已激活", sceneName);
        });
    }
}
```

### 3. 测试 API

```bash
# 获取设备列表
curl http://localhost:8082/api/smarthome/devices

# 添加设备
curl -X POST http://localhost:8082/api/smarthome/device \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "MI_001",
    "device_name": "客厅灯",
    "device_type": "light",
    "platform": "mihome",
    "room": "客厅"
  }'

# 添加交易记录
curl -X POST http://localhost:8082/api/finance/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "type": "expense",
    "category": "餐饮",
    "recorded_by": "爸爸"
  }'

# 获取积分排行榜
curl http://localhost:8082/api/leaderboard
```

---

## 📱 功能使用示例

### 智能家居

```java
// 添加设备
smartHomeService.addDevice("001", "客厅灯", "light", "mihome", "客厅");

// 控制设备
smartHomeService.controlDevice("MI_001", "on", null);
smartHomeService.controlDevice("MI_001", "set_brightness", 80);

// 执行场景
smartHomeService.executeScene("home_mode");  // 回家模式
smartHomeService.executeScene("away_mode");  // 离家模式
```

### 家庭账本

```java
// 手动记账
financeService.addTransaction(50.0, "expense", "餐饮", "午餐", "公司附近", "爸爸");

// 语音记账
financeService.addTransactionByVoice("今天花了 50 块钱吃饭", "爸爸");

// 设置预算
financeService.setBudget("餐饮", 1500.0, "monthly");

// 获取统计
Map<String, Double> stats = financeService.getMonthStats("2026-03");
```

### 家庭任务板

```java
// 创建任务
taskService.createTask("洗碗", "", "爸爸", 10, "2026-03-04", "daily", "妈妈");

// 完成任务
taskService.completeTask("1234567890", "爸爸");

// 获取排行榜
List<Map<String, Object>> leaderboard = taskService.getLeaderboard();

// 创建默认任务
taskService.createDefaultTasks();
```

### 智能购物清单

```java
// 添加物品
shoppingService.addItem("牛奶", "食品", 2, "瓶", "妈妈");

// 语音添加
shoppingService.addItemByVoice("买 5 瓶牛奶", "妈妈");

// 标记已购买
shoppingService.markAsPurchased("1234567890");

// 获取价格对比
Map<String, Double> prices = shoppingService.getPriceComparison("牛奶");
// 返回：{京东：100, 淘宝：95, 拼多多：88, 盒马：105}
```

---

## 🔧 配置说明

### 智能家居平台接入

需要申请各平台 API Key：

- **米家**: https://iot.mi.com/
- **涂鸦**: https://iot.tuya.com/
- **HomeKit**: iOS 原生支持

在 `SmartHomeService` 中配置：

```java
// 米家配置
MiHomeAdapter miHome = new MiHomeAdapter();
miHome.setApiKey("your_mihome_api_key");

// 涂鸦配置
TuyaAdapter tuya = new TuyaAdapter();
tuya.setApiKey("your_tuya_api_key", "your_tuya_secret");
```

### 飞书 Webhook 通知

已在 `FinanceService` 中集成预算预警：

```java
// Webhook URL（已在代码中配置）
https://open.feishu.cn/open-apis/bot/v2/hook/8c164cc1-e173-4011-a53c-75153147de7d
```

---

## 📊 数据库迁移

如果使用 Room 数据库，参考以下 Entity 定义：

```java
@Entity(tableName = "transactions")
public class Transaction {
    @PrimaryKey(autoGenerate = true)
    public int id;
    public double amount;
    public String type;
    public String category;
    public String subcategory;
    public String note;
    public String recordedBy;
    public Date recordedAt;
}

@Entity(tableName = "tasks")
public class Task {
    @PrimaryKey(autoGenerate = true)
    public int id;
    public String taskName;
    public String assignedTo;
    public int points;
    public String status;
    public Date dueDate;
}
```

---

## 🐛 常见问题

### Q: 后端服务启动失败？
A: 检查端口 8082 是否被占用：
```bash
lsof -i :8082
kill -9 <PID>
```

### Q: Android 编译错误？
A: 确保添加以下依赖到 `build.gradle`：
```gradle
implementation 'androidx.recyclerview:recyclerview:1.3.0'
implementation 'com.google.code.gson:gson:2.10.1'
```

### Q: 如何测试语音功能？
A: 暂时使用文本模拟，实际需集成语音识别：
```java
// 使用系统语音识别
Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
startActivityForResult(intent, VOICE_REQUEST);
```

---

## 📈 下一步

1. ✅ 完成核心服务代码
2. ⏳ 创建 Activity 实现类
3. ⏳ 集成语音识别（DashScope）
4. ⏳ 对接电商平台 API
5. ⏳ 添加数据可视化图表

---

**有问题？** 查看 `docs/FEATURE_PROPOSAL.md` 获取详细设计文档。
