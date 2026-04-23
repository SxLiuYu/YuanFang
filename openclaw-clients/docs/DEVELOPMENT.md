# OpenClaw 开发指南

**版本**: v1.0  
**更新日期**: 2026-03-19

---

## 目录

1. [开发环境搭建](#一开发环境搭建)
2. [项目构建](#二项目构建)
3. [调试指南](#三调试指南)
4. [代码规范](#四代码规范)
5. [Git 工作流](#五git-工作流)
6. [常见问题](#六常见问题)

---

## 一、开发环境搭建

### 1.1 后端环境

**系统要求**：
- Python 3.10 或更高版本
- pip 包管理器
- SQLite 3

**安装步骤**：

```bash
# 1. 克隆仓库
git clone https://github.com/SxLiuYu/openclaw-clients.git
cd openclaw-clients

# 2. 创建虚拟环境
cd backend
python -m venv venv

# Windows 激活
venv\Scripts\activate

# Linux/Mac 激活
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp ../config/config.example.yaml ../config/config.yaml
# 编辑 config.yaml，填入 API Key

# 5. 启动开发服务器
python main.py

# 访问 API 文档
# http://localhost:8082/docs
```

**IDE 推荐**：
- VS Code + Python 插件
- PyCharm

**VS Code 推荐插件**：
- Python
- Pylance
- Python Docstring Generator
- autoDocstring

### 1.2 Windows 客户端环境

**系统要求**：
- Windows 10 1809 或更高版本
- .NET 8 SDK
- Visual Studio 2022 或 VS Code

**安装步骤**：

```bash
# 1. 安装 .NET 8 SDK
# 下载地址: https://dotnet.microsoft.com/download/dotnet/8.0

# 2. 验证安装
dotnet --version
# 应显示: 8.0.xxx

# 3. 进入项目目录
cd windows-desktop/OpenClaw.Desktop

# 4. 还原依赖
dotnet restore

# 5. 构建项目
dotnet build

# 6. 运行项目
dotnet run
```

**IDE 推荐**：
- Visual Studio 2022 (Community 版免费)
- VS Code + C# Dev Kit

**VS Code 推荐插件**：
- C#
- C# Dev Kit
- XAML Styler
- Material Design Toolkit

### 1.3 推荐工具

**API 测试**：
- Postman
- curl
- httpie

**数据库管理**：
- DB Browser for SQLite
- SQLite Studio

**Git 客户端**：
- Git Bash
- GitHub Desktop
- Sourcetree

---

## 二、项目构建

### 2.1 后端构建

**开发模式**：
```bash
cd backend
python main.py
```

**生产模式**：
```bash
# 使用 Gunicorn + Uvicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8082

# 或使用 Docker
docker build -t openclaw-backend .
docker run -d -p 8082:8082 openclaw-backend
```

**Docker 构建**：
```bash
cd backend
docker build -t openclaw-backend .
docker-compose up -d
```

### 2.2 Windows 客户端构建

**调试构建**：
```bash
cd windows-desktop/OpenClaw.Desktop
dotnet build
dotnet run
```

**发布构建**：
```bash
# 发布为自包含应用（无需安装 .NET）
dotnet publish -c Release -r win-x64 --self-contained

# 发布为单文件
dotnet publish -c Release -r win-x64 --self-contained /p:PublishSingleFile=true

# 发布并裁剪（减小体积）
dotnet publish -c Release -r win-x64 --self-contained /p:PublishSingleFile=true /p:PublishTrimmed=true
```

**输出位置**：
```
bin/Release/net8.0-windows/win-x64/publish/OpenClaw.Desktop.exe
```

**创建安装包**：
```bash
# 使用 MSIX 打包（需要 Visual Studio）
# 或使用 Inno Setup、NSIS 等工具
```

---

## 三、调试指南

### 3.1 后端调试

**VS Code 调试配置**（`.vscode/launch.json`）：
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--port",
        "8082"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

**调试技巧**：
```python
# 1. 打印调试
print(f"Debug: {variable}")

# 2. 断点调试
import pdb; pdb.set_trace()

# 3. 日志调试
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Debug info: {variable}")

# 4. 检查 API 响应
import pprint
pprint.pprint(response.json())
```

**常用调试命令**：
```bash
# 测试健康检查
curl http://localhost:8082/health

# 测试语音命令
curl -X POST http://localhost:8082/api/v1/voice/command \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}'

# 查看数据库
sqlite3 data/family.db
sqlite> SELECT * FROM family_groups;
```

### 3.2 Windows 客户端调试

**Visual Studio 调试**：
1. 设置断点（F9）
2. 启动调试（F5）
3. 单步执行（F10/F11）
4. 查看变量（鼠标悬停或监视窗口）

**VS Code 调试配置**（`.vscode/launch.json`）：
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch WPF App",
      "type": "coreclr",
      "request": "launch",
      "program": "${workspaceFolder}/windows-desktop/OpenClaw.Desktop/bin/Debug/net8.0-windows/OpenClaw.Desktop.dll",
      "cwd": "${workspaceFolder}/windows-desktop/OpenClaw.Desktop"
    }
  ]
}
```

**调试技巧**：
```csharp
// 1. 输出调试信息
System.Diagnostics.Debug.WriteLine($"Debug: {variable}");

// 2. 断言
System.Diagnostics.Debug.Assert(condition, "Message");

// 3. 条件断点
// 在 Visual Studio 中右键断点 -> Conditions

// 4. 即时窗口
// 在断点处按 Ctrl+D, I 打开即时窗口
```

**查看绑定错误**：
```xml
<!-- 在 App.xaml 中启用绑定调试 -->
<Application.Resources>
    <presentationFramework:BindingTraceListener />
</Application.Resources>
```

**查看 MVVM 问题**：
```csharp
// 在 ViewModel 中添加调试输出
partial void OnSelectedMenuItemChanged(MenuItem? value)
{
    System.Diagnostics.Debug.WriteLine($"Selected: {value?.Title}");
}
```

---

## 四、代码规范

### 4.1 Python 代码规范

**遵循 PEP 8**：
- 使用 4 空格缩进
- 行长度不超过 88 字符
- 使用 snake_case 命名函数和变量
- 使用 PascalCase 命名类

**示例**：
```python
# 好的命名
class VoiceEnhancedService:
    def get_suggestions(self, user_id: str) -> List[VoiceSuggestion]:
        pass

# 不好的命名
class voiceService:
    def GetSuggestions(self, userId) -> list:
        pass
```

**类型注解**：
```python
# 必须使用类型注解
async def create_group(self, request: FamilyGroupCreate) -> Dict[str, Any]:
    pass
```

**文档字符串**：
```python
async def calculate_health_score(self, user_id: str) -> float:
    """计算健康评分
    
    Args:
        user_id: 用户 ID
        
    Returns:
        健康评分（0-100）
        
    Raises:
        ValueError: 如果用户 ID 为空
    """
    pass
```

**导入顺序**：
```python
# 1. 标准库
import os
import sys
from datetime import datetime

# 2. 第三方库
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

# 3. 本地模块
from services.voice_service import voice_service
```

### 4.2 C# 代码规范

**命名规范**：
- 类、方法：PascalCase
- 私有字段：_camelCase
- 局部变量、参数：camelCase
- 常量：PascalCase 或全部大写

**示例**：
```csharp
// 好的命名
public class VoiceControlViewModel : BaseViewModel
{
    private readonly VoiceApiService _voiceApiService;
    private string _recognizedText = "";
    
    public ObservableCollection<VoiceSuggestion> Suggestions { get; } = new();
    
    public async Task ProcessCommandAsync(string text)
    {
        var response = await _voiceApiService.ProcessCommandAsync(text);
    }
}
```

**XAML 命名规范**：
```xml
<!-- 控件命名：x:Name 使用 PascalCase -->
<Button x:Name="SubmitButton" Content="提交" />

<!-- 资源键：使用 PascalCase -->
<Grid.Resources>
    <Style x:Key="CardStyle" TargetType="Border">
    </Style>
</Grid.Resources>
```

**注释规范**：
```csharp
/// <summary>
/// 处理语音命令
/// </summary>
/// <param name="text">语音文本</param>
/// <returns>处理结果</returns>
public async Task<VoiceCommandResponse> ProcessCommandAsync(string text)
{
    // 实现...
}
```

### 4.3 提交信息规范

**遵循 Conventional Commits**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建过程或辅助工具变动

**示例**：
```
feat(voice): 添加智能建议功能

- 实现基于时间的建议
- 实现基于习惯的建议
- 实现综合评分算法

Closes #123
```

---

## 五、Git 工作流

### 5.1 分支策略

```
main (主分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/voice-control (功能分支)
  │     ├── feature/family-group (功能分支)
  │     └── bugfix/api-error (修复分支)
  │
  └── release/v1.0.0 (发布分支)
```

### 5.2 工作流程

```bash
# 1. 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. 开发并提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送到远程
git push origin feature/new-feature

# 4. 创建 Pull Request
# 在 GitHub 上创建 PR，目标分支为 develop

# 5. 代码审查通过后合并
# 合并后删除功能分支
git checkout develop
git pull origin develop
git branch -d feature/new-feature
```

### 5.3 合并请求规范

**PR 标题**：
```
feat: 添加语音控制功能
```

**PR 描述模板**：
```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 重构
- [ ] 文档更新

## 变更说明
简要描述本次变更的内容

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过

## 相关 Issue
Closes #123
```

---

## 六、常见问题

### 6.1 后端问题

**Q: 启动后端报错 "ModuleNotFoundError"？**
```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 重新安装依赖
pip install -r requirements.txt
```

**Q: API 请求返回 500 错误？**
```python
# 检查日志
tail -f logs/app.log

# 或在代码中添加异常处理
try:
    result = await some_function()
except Exception as e:
    logging.error(f"Error: {e}", exc_info=True)
    raise
```

**Q: 数据库文件在哪里？**
```
data/
├── family.db
├── hardware.db
├── analytics.db
└── voice_enhanced.db
```

### 6.2 Windows 客户端问题

**Q: 构建失败 "NuGet 包还原失败"？**
```bash
# 清理并重新还原
dotnet clean
dotnet restore --force
dotnet build
```

**Q: 运行时崩溃 "FileNotFoundException"？**
```csharp
// 检查 appsettings.json 是否存在
// 检查输出目录是否有所有依赖文件
dotnet publish --self-contained
```

**Q: XAML 绑定不工作？**
```xml
<!-- 检查 DataContext 设置 -->
<Window.DataContext>
    <vm:MainViewModel/>
</Window.DataContext>

<!-- 检查属性是否实现 INotifyPropertyChanged -->
<!-- 使用 CommunityToolkit.Mvvm 的 ObservableProperty -->
```

**Q: API 调用失败？**
```csharp
// 检查后端是否启动
// 检查 API 地址是否正确
// 检查网络连接
var url = "http://localhost:8082/api/v1/health";
```

### 6.3 调试技巧

**查看 SQL 查询**：
```python
# 在 SQLite 中启用日志
import sqlite3
conn = sqlite3.connect(':memory:')
conn.set_trace_callback(print)
```

**查看 HTTP 请求**：
```python
# 使用 httpx 的调试模式
import httpx
import logging

logging.basicConfig(level=logging.DEBUG)
client = httpx.Client()
```

**查看 WPF 绑定**：
```xml
<!-- 在 Output 窗口查看绑定错误 -->
<!-- 或使用 Snoop 工具 -->
```

---

## 附录

### A. 有用的命令

```bash
# 后端
python main.py                    # 启动服务
pytest tests/                     # 运行测试
flake8 .                          # 代码检查
black .                           # 代码格式化

# Windows 客户端
dotnet build                      # 构建
dotnet run                        # 运行
dotnet test                       # 测试
dotnet publish -c Release         # 发布
```

### B. 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [.NET 文档](https://docs.microsoft.com/dotnet/)
- [WPF 文档](https://docs.microsoft.com/dotnet/desktop/wpf/)
- [MaterialDesign 文档](https://materialdesigninxaml.net/)
- [CommunityToolkit.Mvvm 文档](https://docs.microsoft.com/dotnet/communitytoolkit/mvvm/)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19