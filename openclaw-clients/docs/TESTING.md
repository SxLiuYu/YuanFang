# OpenClaw 测试指南

**版本**: v1.0  
**更新日期**: 2026-03-19

---

## 目录

1. [测试策略](#一测试策略)
2. [后端测试](#二后端测试)
3. [Windows 客户端测试](#三windows-客户端测试)
4. [API 测试](#四api-测试)
5. [端到端测试](#五端到端测试)

---

## 一、测试策略

### 1.1 测试金字塔

```
        ┌─────────────┐
        │   E2E 测试   │  (少量)
        └─────────────┘
      ┌───────────────────┐
      │    集成测试        │  (中等)
      └───────────────────┘
    ┌─────────────────────────┐
    │      单元测试            │  (大量)
    └─────────────────────────┘
```

### 1.2 测试类型

| 测试类型 | 覆盖率目标 | 执行频率 |
|---------|-----------|---------|
| 单元测试 | > 80% | 每次提交 |
| 集成测试 | > 70% | 每日 |
| API 测试 | 100% 端点 | 每次部署 |
| E2E 测试 | 核心流程 | 每周 |

### 1.3 测试工具

**后端**：
- pytest - 单元测试框架
- pytest-asyncio - 异步测试
- httpx - API 测试

**Windows 客户端**：
- xUnit - 单元测试框架
- Moq - Mock 框架

**API 测试**：
- Postman
- curl

---

## 二、后端测试

### 2.1 测试环境设置

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov httpx

# 创建测试配置
cp config/config.example.yaml config/config.test.yaml
```

### 2.2 单元测试示例

**测试语音服务**：

```python
# tests/test_voice_enhanced_service.py
import pytest
from services.voice_enhanced_service import VoiceEnhancedService

@pytest.fixture
def voice_service():
    return VoiceEnhancedService(db_path=":memory:")

@pytest.mark.asyncio
async def test_parse_device_control_turn_on(voice_service):
    """测试设备控制命令解析 - 打开设备"""
    text = "打开客厅的灯"
    intent, slots = await voice_service.parse_device_control(text)
    
    assert intent == "device_control"
    assert slots["action"] == "turn_on"
    assert slots["device"] == "客厅的灯"

@pytest.mark.asyncio
async def test_parse_device_control_turn_off(voice_service):
    """测试设备控制命令解析 - 关闭设备"""
    text = "关闭空调"
    intent, slots = await voice_service.parse_device_control(text)
    
    assert intent == "device_control"
    assert slots["action"] == "turn_off"
    assert slots["device"] == "空调"

@pytest.mark.asyncio
async def test_parse_scene_control(voice_service):
    """测试场景控制命令解析"""
    text = "我要睡觉了"
    intent, slots = await voice_service.parse_scene_control(text)
    
    assert intent == "scene_control"
    assert slots["scene"] == "sleep"

@pytest.mark.asyncio
async def test_parse_unknown_command(voice_service):
    """测试无法识别的命令"""
    text = "随便说点什么"
    intent, slots = await voice_service.parse_device_control(text)
    
    assert intent == "unknown"
```

**测试家庭服务**：

```python
# tests/test_family_service.py
import pytest
from services.family_service import FamilyService, FamilyGroupCreate

@pytest.fixture
def family_service():
    return FamilyService(db_path=":memory:")

@pytest.mark.asyncio
async def test_create_group(family_service):
    """测试创建家庭群组"""
    request = FamilyGroupCreate(name="测试家庭", owner_id="user_001")
    result = await family_service.create_group(request)
    
    assert result["success"] == True
    assert "group_id" in result
    assert "invite_code" in result
    assert len(result["invite_code"]) == 8

@pytest.mark.asyncio
async def test_join_group(family_service):
    """测试加入家庭群组"""
    # 创建群组
    create_request = FamilyGroupCreate(name="测试家庭", owner_id="user_001")
    create_result = await family_service.create_group(create_request)
    invite_code = create_result["invite_code"]
    
    # 加入群组
    join_result = await family_service.join_group(invite_code, "user_002", "测试用户")
    
    assert join_result["success"] == True
    assert "group_id" in join_result

@pytest.mark.asyncio
async def test_get_group(family_service):
    """测试获取群组详情"""
    # 创建群组
    create_request = FamilyGroupCreate(name="测试家庭", owner_id="user_001")
    create_result = await family_service.create_group(create_request)
    group_id = create_result["group_id"]
    
    # 获取群组
    group = await family_service.get_group(group_id)
    
    assert group is not None
    assert group["name"] == "测试家庭"
    assert group["owner_id"] == "user_001"
    assert len(group["members"]) == 1
```

### 2.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_voice_enhanced_service.py

# 运行特定测试用例
pytest tests/test_voice_enhanced_service.py::test_parse_device_control_turn_on

# 显示覆盖率
pytest --cov=services --cov-report=html

# 详细输出
pytest -v

# 并行运行
pytest -n auto
```

---

## 三、Windows 客户端测试

### 3.1 单元测试项目

```xml
<!-- OpenClaw.Desktop.Tests/OpenClaw.Desktop.Tests.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.4.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.4.5" />
    <PackageReference Include="Moq" Version="4.20.69" />
  </ItemGroup>
</Project>
```

### 3.2 ViewModel 测试示例

```csharp
// ViewModels.Tests/VoiceControlViewModelTests.cs
using Xunit;
using Moq;
using OpenClaw.Desktop.Services.Api;

public class VoiceControlViewModelTests
{
    private readonly Mock<VoiceApiService> _mockApiService;
    private readonly VoiceControlViewModel _viewModel;
    
    public VoiceControlViewModelTests()
    {
        _mockApiService = new Mock<VoiceApiService>();
        _viewModel = new VoiceControlViewModel(_mockApiService.Object);
    }
    
    [Fact]
    public void InitialState_ShouldHaveDefaultValues()
    {
        // Assert
        Assert.False(_viewModel.IsListening);
        Assert.Equal("按下麦克风开始说话...", _viewModel.RecognizedText);
        Assert.Empty(_viewModel.Suggestions);
    }
    
    [Fact]
    public async Task ProcessCommand_ShouldUpdateResponse()
    {
        // Arrange
        var expectedResponse = new VoiceCommandResponse
        {
            Success = true,
            Message = "好的，已为您打开客厅的灯"
        };
        
        _mockApiService
            .Setup(s => s.ProcessCommandAsync("打开客厅的灯"))
            .ReturnsAsync(expectedResponse);
        
        // Act
        await _viewModel.ProcessCommandAsync("打开客厅的灯");
        
        // Assert
        Assert.Equal("好的，已为您打开客厅的灯", _viewModel.ResponseMessage);
    }
    
    [Fact]
    public void Clear_ShouldResetState()
    {
        // Arrange
        _viewModel.RecognizedText = "测试文本";
        _viewModel.ResponseMessage = "测试响应";
        _viewModel.Suggestions.Add(new VoiceSuggestion());
        
        // Act
        _viewModel.Clear();
        
        // Assert
        Assert.Equal("按下麦克风开始说话...", _viewModel.RecognizedText);
        Assert.Empty(_viewModel.ResponseMessage);
        Assert.Empty(_viewModel.Suggestions);
    }
}
```

### 3.3 运行测试

```bash
# 运行所有测试
dotnet test

# 运行特定测试
dotnet test --filter "FullyQualifiedName~VoiceControlViewModelTests"

# 显示覆盖率（需要安装 coverlet）
dotnet test /p:CollectCoverage=true

# 生成覆盖率报告
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover
```

---

## 四、API 测试

### 4.1 Postman 集合

**导入 Postman 集合**：
```json
{
  "info": {
    "name": "OpenClaw API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Voice API",
      "item": [
        {
          "name": "Process Voice Command",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/voice/command",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"text\": \"打开客厅的灯\"\n}"
            }
          }
        },
        {
          "name": "Get Suggestions",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/voice/suggestions"
          }
        }
      ]
    },
    {
      "name": "Family API",
      "item": [
        {
          "name": "Create Family Group",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/v1/family/groups",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"测试家庭\",\n  \"owner_id\": \"user_001\"\n}"
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8082"
    }
  ]
}
```

### 4.2 curl 测试脚本

```bash
#!/bin/bash
# test_api.sh

BASE_URL="http://localhost:8082"

echo "=== 测试健康检查 ==="
curl -s $BASE_URL/health | jq .

echo "\n=== 测试语音命令 ==="
curl -s -X POST $BASE_URL/api/v1/voice/command \
  -H "Content-Type: application/json" \
  -d '{"text": "打开客厅的灯"}' | jq .

echo "\n=== 测试智能建议 ==="
curl -s $BASE_URL/api/v1/voice/suggestions | jq .

echo "\n=== 测试创建家庭群组 ==="
curl -s -X POST $BASE_URL/api/v1/family/groups \
  -H "Content-Type: application/json" \
  -d '{"name": "测试家庭", "owner_id": "user_001"}' | jq .

echo "\n=== 测试获取健康评分 ==="
curl -s "$BASE_URL/api/v1/analytics/health/score?user_id=user_001" | jq .
```

### 4.3 自动化 API 测试

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client):
    """测试健康检查"""
    response = await client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_voice_command(client):
    """测试语音命令"""
    response = await client.post(
        "/api/v1/voice/command",
        json={"text": "打开客厅的灯"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True

@pytest.mark.asyncio
async def test_create_family_group(client):
    """测试创建家庭群组"""
    response = await client.post(
        "/api/v1/family/groups",
        json={"name": "测试家庭", "owner_id": "user_001"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "group_id" in data
    assert "invite_code" in data
```

---

## 五、端到端测试

### 5.1 测试场景

**场景 1：语音控制流程**
```
1. 用户打开应用
2. 用户点击语音按钮
3. 用户说"打开客厅的灯"
4. 系统识别并执行
5. 系统反馈结果
```

**场景 2：家庭协作流程**
```
1. 用户创建家庭群组
2. 其他成员加入群组
3. 成员分享位置
4. 创建共享日程
```

**场景 3：硬件集成流程**
```
1. 用户扫描蓝牙设备
2. 用户配对设备
3. 同步手表数据
4. 查看健康数据
```

### 5.2 E2E 测试脚本

```python
# tests/test_e2e.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_voice_control_flow():
    """测试语音控制完整流程"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 获取智能建议
        response = await client.get("/api/v1/voice/suggestions")
        assert response.status_code == 200
        suggestions = response.json()
        
        # 2. 执行语音命令
        response = await client.post(
            "/api/v1/voice/command",
            json={"text": "我要睡觉了"}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["intent"] == "scene_control"

@pytest.mark.asyncio
async def test_family_collaboration_flow():
    """测试家庭协作完整流程"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 创建群组
        response = await client.post(
            "/api/v1/family/groups",
            json={"name": "E2E测试家庭", "owner_id": "owner_001"}
        )
        assert response.status_code == 200
        group_data = response.json()
        group_id = group_data["group_id"]
        invite_code = group_data["invite_code"]
        
        # 2. 成员加入
        response = await client.post(
            f"/api/v1/family/join?invite_code={invite_code}&user_id=member_001&name=测试成员"
        )
        assert response.status_code == 200
        
        # 3. 分享位置
        response = await client.post(
            "/api/v1/family/location/share",
            json={
                "user_id": "member_001",
                "latitude": 39.9042,
                "longitude": 116.4074
            }
        )
        assert response.status_code == 200
        
        # 4. 创建共享日程
        response = await client.post(
            "/api/v1/family/calendar/shared",
            json={
                "group_id": group_id,
                "title": "家庭聚餐",
                "start_time": "2026-03-20T12:00:00"
            }
        )
        assert response.status_code == 200
```

### 5.3 性能测试

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_concurrent_requests():
    """测试并发请求"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 发送 100 个并发请求
        tasks = [
            client.get("/health")
            for _ in range(100)
        ]
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 所有请求都应该成功
        assert all(r.status_code == 200 for r in responses)
        
        # 响应时间应该小于 5 秒
        assert (end_time - start_time) < 5
        
        print(f"\n100 requests completed in {end_time - start_time:.2f}s")
```

---

## 附录

### A. 测试覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=services --cov-report=html --cov-report=term

# 打开报告
open htmlcov/index.html
```

### B. CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=services --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19