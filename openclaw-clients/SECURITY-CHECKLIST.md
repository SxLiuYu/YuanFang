# 安全检查清单

本文档记录项目的安全检查项和已修复的安全问题。

## 立即处理

### 已泄露的 API Key

| API | Key 前缀 | 状态 | 文件 | 处理日期 |
|-----|----------|------|------|----------|
| 博查 API | `sk-f5c0342e...` | 🔴 已泄露 | `NewsService.java:24` | 待轮换 |

### 轮换步骤

**博查 API Key 轮换：**

1. 登录博查控制台
   ```
   https://api.bocha.cn
   ```

2. 进入 API Key 管理
   - 找到已泄露的 Key
   - 点击"删除"

3. 创建新 Key
   - 点击"创建新 Key"
   - 复制新 Key

4. 更新服务器配置
   ```bash
   # 在服务器上
   export BOCHA_API_KEY=新的API_KEY
   
   # 或更新 .env 文件
   echo "BOCHA_API_KEY=新的API_KEY" >> /path/to/.env
   
   # 重启服务
   systemctl restart openclaw-backend
   ```

5. 验证新 Key
   ```bash
   curl -H "Authorization: Bearer 新的API_KEY" \
        https://api.bocha.cn/v1/web-search
   ```

---

## 已修复的安全问题

### 2026-03-13 修复记录

| 问题 | 严重程度 | 修复方式 |
|------|----------|----------|
| API Key 硬编码 | 🔴 严重 | 改为动态配置 |
| 服务器 IP 硬编码 | 🟡 中等 | 改为 BuildConfig 配置 |
| Debug 模式运行 | 🟡 中等 | 改为环境变量控制 |
| Web API Key 明文存储 | 🟡 中等 | 移除客户端 Key，走服务端代理 |
| 大文件入库 | 🟡 中等 | 添加 .gitignore，移除跟踪 |

### 修复详情

#### 1. API Key 硬编码
```diff
// NewsService.java
- private static final String BOCHA_API_KEY = "sk-f5c0342e1a6e43d7b77b24d3fb268b81";
+ private String bochaApiKey;
+ public void setBochaApiKey(String apiKey) { this.bochaApiKey = apiKey; }
```

#### 2. 服务器地址硬编码
```diff
// SecureConfig.java
- public static final String DEFAULT_SERVER_URL = "http://123.57.107.21:8081";
+ public static final String DEFAULT_SERVER_URL = BuildConfig.DEFAULT_SERVER_URL;
```

#### 3. Debug 模式
```diff
// tmall_ai_skill.py
- app.run(host='0.0.0.0', port=8083, ssl_context='adhoc', debug=True)
+ DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
+ app.run(host='0.0.0.0', port=8083, ssl_context='adhoc', debug=DEBUG_MODE)
```

---

## 安全编码规范

### 禁止事项

| 禁止 | 原因 | 替代方案 |
|------|------|----------|
| 硬编码 API Key | 代码泄露导致 Key 泄露 | 环境变量/加密存储 |
| 明文存储密码 | 数据库泄露导致密码泄露 | 使用加密存储 |
| HTTP 明文传输 | 中间人攻击 | 使用 HTTPS |
| 提交 .env 文件 | 敏感信息泄露 | .gitignore 排除 |
| e.printStackTrace() | 日志可能包含敏感信息 | 使用 Log.e() |
| Debug 模式部署 | 暴露调试信息 | 生产环境禁用 |

### 推荐做法

#### Android
```java
// ✅ 正确：使用加密存储
SecureConfig config = SecureConfig.getInstance(context);
config.setApiKey("sk-xxxxx");

// ❌ 错误：硬编码
private static final String API_KEY = "sk-xxxxx";
```

#### Python
```python
# ✅ 正确：从环境变量读取
import os
api_key = os.getenv('DASHSCOPE_API_KEY')

# ❌ 错误：硬编码
api_key = "sk-xxxxx"
```

#### JavaScript
```javascript
// ✅ 正确：从配置文件读取
const serverUrl = process.env.OPENCLAW_SERVER_URL;

// ❌ 错误：硬编码
const serverUrl = "http://123.57.107.21:8081";
```

---

## 定期检查项

### 每周检查
- [ ] 检查 `.env` 文件是否在 `.gitignore` 中
- [ ] 检查日志是否打印敏感信息
- [ ] 检查依赖包是否有安全漏洞

### 每月检查
- [ ] 检查代码中是否有硬编码的敏感信息
- [ ] 审查新增代码的安全合规性
- [ ] 检查服务器访问日志

### 每 90 天
- [ ] 轮换所有 API Key
- [ ] 更新依赖包版本
- [ ] 审查权限配置

---

## 应急响应流程

### 发现安全漏洞

1. **评估影响**
   - 确定受影响的系统
   - 确定泄露的数据类型

2. **立即止损**
   - 轮换相关 API Key
   - 禁用受影响的服务
   - 通知相关方

3. **修复漏洞**
   - 修改代码
   - 部署修复
   - 验证修复效果

4. **事后总结**
   - 记录事件经过
   - 分析根本原因
   - 制定预防措施

### 联系方式

- 项目负责人: [GitHub Issues](https://github.com/SxLiuYu/openclaw-clients/issues)
- 安全问题: 请通过 GitHub Security Advisories 私密报告

---

## 安全扫描工具

### 推荐工具

| 工具 | 用途 | 链接 |
|------|------|------|
| GitHub Dependabot | 依赖漏洞扫描 | 内置 |
| SonarQube | 代码安全扫描 | sonarqube.org |
| OWASP ZAP | Web 安全测试 | zapproxy.org |
| GitLeaks | 敏感信息扫描 | github.com/gitleaks/gitleaks |

### 本地扫描

```bash
# 使用 GitLeaks 扫描敏感信息
gitleaks detect --source . --verbose

# 使用 Trivy 扫描依赖漏洞
trivy fs .
```

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-03-13 | 创建安全检查清单，记录已修复问题 |