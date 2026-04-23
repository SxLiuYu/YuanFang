# 小红书搜索功能

为家庭助手添加小红书内容搜索能力，可以搜索美食、家居、旅行等各类笔记。

## 功能特性

- ✅ 关键词搜索
- ✅ 获取笔记详情
- ✅ 检查登录状态
- ✅ 结构化数据返回（标题、作者、点赞数、封面图等）

## 前置要求

### 1. 安装 mcporter

```bash
npm install -g mcporter
```

### 2. 启动小红书 MCP 服务

```bash
# Docker 方式（推荐）
docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp

# 或使用 platform 参数（ARM64 设备）
docker run -d --name xiaohongshu-mcp -p 18060:18060 --platform linux/amd64 xpzouying/xiaohongshu-mcp
```

### 3. 配置 mcporter

```bash
mcporter config add xiaohongshu http://localhost:18060/mcp
```

### 4. 登录小红书

```bash
# 获取登录二维码
mcporter call xiaohongshu.get_login_qrcode

# 检查登录状态
mcporter call xiaohongshu.check_login_status
```

## API 接口

### 1. 搜索笔记

**请求**
```
GET /api/xiaohongshu/search?keyword=美食推荐&limit=10
```

**参数**
- `keyword` (必填): 搜索关键词
- `limit` (可选): 返回结果数量，默认 10

**响应**
```json
{
  "success": true,
  "keyword": "美食推荐",
  "count": 10,
  "results": [
    {
      "id": "693e5aa3000000001e00d307",
      "title": "只说实话系列 - 山石榴贵州菜",
      "type": "normal",
      "author": {
        "user_id": "5fcb8ba300000000010038dc",
        "nickname": "🍫🍰",
        "avatar": "https://..."
      },
      "cover_image": "http://...",
      "stats": {
        "likes": "98",
        "collects": "53",
        "comments": "1",
        "shares": "64"
      },
      "xsec_token": "AB-7PYgDHxUhAj1kSqgPnIoay911DOt0mRl0u9DPjA8hQw=",
      "url": "https://www.xiaohongshu.com/explore/693e5aa3000000001e00d307"
    }
  ],
  "error": null
}
```

### 2. 获取笔记详情

**请求**
```
GET /api/xiaohongshu/detail?feed_id=xxx&xsec_token=xxx&load_comments=false
```

**参数**
- `feed_id` (必填): 笔记 ID
- `xsec_token` (必填): 访问令牌（从搜索结果获取）
- `load_comments` (可选): 是否加载评论，默认 false

**响应**
```json
{
  "success": true,
  "data": {
    // 笔记详细信息
  }
}
```

### 3. 检查登录状态

**请求**
```
GET /api/xiaohongshu/status
```

**响应**
```json
{
  "logged_in": true,
  "message": "已登录"
}
```

## 使用示例

### Python 客户端

```python
import requests

# 搜索美食推荐
response = requests.get('http://localhost:8082/api/xiaohongshu/search', params={
    'keyword': '美食推荐',
    'limit': 5
})

result = response.json()
if result['success']:
    for note in result['results']:
        print(f"{note['title']} - {note['author']['nickname']}")
        print(f"  点赞：{note['stats']['likes']}")
        print(f"  链接：{note['url']}\n")
```

### 家庭助手语音指令

```
"帮我搜索小红书上的美食推荐"
"找一下家居装修的笔记"
"看看最近流行的旅行攻略"
```

## 测试

```bash
# 启动家庭助手 API
cd /home/admin/.openclaw/workspace/openclaw-clients/backend/services
python3 family_services_api.py

# 运行测试脚本
python3 test_xiaohongshu.py
```

## 注意事项

1. **搜索速度**: 首次搜索可能需要 10-30 秒（建立连接 + 网络请求）
2. **登录状态**: 搜索功能需要小红书账号已登录
3. **请求限制**: 避免短时间内大量请求，可能触发风控
4. **Docker 服务**: 确保 xiaohongshu-mcp 容器运行正常

## 故障排查

### 问题：搜索返回"Unknown MCP server"

**解决**: 检查 mcporter 配置
```bash
mcporter config list
# 确认 xiaohongshu 在列表中

# 如不存在，重新配置
mcporter config add xiaohongshu http://localhost:18060/mcp
```

### 问题：搜索超时

**解决**: 
1. 检查 Docker 容器状态
```bash
docker ps | grep xiaohongshu
```

2. 测试 MCP 连接
```bash
mcporter call xiaohongshu.check_login_status
```

3. 重启 MCP 服务
```bash
docker restart xiaohongshu-mcp
```

### 问题：未登录

**解决**: 扫码登录
```bash
mcporter call xiaohongshu.get_login_qrcode
# 使用小红书 APP 扫描二维码
```

## 相关文件

- 服务实现：`xiaohongshu_search_service.py`
- API 接口：`family_services_api.py`
- 测试脚本：`test_xiaohongshu.py`
- 本文档：`XIAOHONGSHU_SEARCH.md`
