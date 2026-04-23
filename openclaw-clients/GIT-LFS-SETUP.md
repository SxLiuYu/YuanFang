# Git LFS 配置指南

本文档说明如何配置 Git Large File Storage (LFS) 管理项目中的大文件。

## 什么是 Git LFS？

Git LFS 是 Git 的扩展，用于管理大型文件。它将大文件存储在远程服务器上，只在本地保留指针文件，从而减小仓库体积。

## 当前配置的大文件类型

| 文件类型 | 扩展名 | 说明 |
|----------|--------|------|
| AI 模型 | `.pth`, `.pt`, `.bin`, `.h5`, `.onnx` | 深度学习模型文件 |
| 压缩包 | `.zip`, `.tar.gz`, `.tgz`, `.7z` | 数据集和资源包 |
| 视频 | `.mp4`, `.mov` | 媒体文件 |
| 音频 | `.wav`, `.mp3` | 音频文件 |
| 数据 | `.parquet`, `.arrow`, `.jsonl` | 大型数据文件 |

## 安装 Git LFS

### Windows
```bash
# 方式 1: 使用安装包
# 下载: https://git-lfs.github.com/

# 方式 2: 使用 Chocolatey
choco install git-lfs

# 方式 3: 使用 Scoop
scoop install git-lfs
```

### macOS
```bash
# 使用 Homebrew
brew install git-lfs
```

### Linux
```bash
# Debian/Ubuntu
sudo apt-get install git-lfs

# CentOS/RHEL
sudo yum install git-lfs

# Arch Linux
sudo pacman -S git-lfs
```

## 初始化配置

### 1. 安装 Git LFS 扩展
```bash
git lfs install
```

### 2. 跟踪大文件类型
```bash
# 跟踪模型文件
git lfs track "*.pth"
git lfs track "*.pt"
git lfs track "*.bin"

# 跟踪压缩包
git lfs track "*.zip"
git lfs track "*.tar.gz"
```

### 3. 提交 .gitattributes
```bash
git add .gitattributes
git commit -m "chore: configure Git LFS"
```

## 恢复已删除的大文件

如果大文件之前已被提交到 Git，需要迁移到 LFS：

```bash
# 迁移特定文件
git lfs migrate import --include="craft_mlt_25k.pth,zh_sim_g2.zip,english_g2.zip" --everything

# 强制推送到远程
git push --force
```

## 验证配置

### 检查 LFS 状态
```bash
git lfs status
```

### 检查跟踪的文件
```bash
git lfs ls-files
```

### 检查 .gitattributes
```bash
cat .gitattributes
```

## 克隆包含 LFS 的仓库

### 普通克隆
```bash
git clone https://github.com/SxLiuYu/openclaw-clients.git
# LFS 文件会自动下载
```

### 跳过 LFS 文件（节省时间）
```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/SxLiuYu/openclaw-clients.git
```

### 稍后下载 LFS 文件
```bash
git lfs pull
```

## 常见问题

### Q: 推送时提示 LFS 配额不足
A: GitHub 免费账户 LFS 配额为 1GB，带宽 1GB/月。
解决方案：
1. 升级 GitHub Pro
2. 使用其他 LFS 服务（如 GitLab、Bitbucket）
3. 自建 LFS 服务器

### Q: LFS 文件下载失败
```bash
# 检查 LFS 配置
git lfs env

# 重新拉取
git lfs pull --include="path/to/file"
```

### Q: 如何取消 LFS 跟踪
```bash
# 从 LFS 移除文件
git lfs untrack "*.zip"

# 迁移回普通 Git
git lfs migrate export --include="*.zip" --everything
```

## 本项目的大文件

当前项目中使用 LFS 管理的文件：

| 文件 | 大小 | 说明 |
|------|------|------|
| `craft_mlt_25k.pth` | ~80MB | CRAFT 文本检测模型 |
| `zh_sim_g2.zip` | ~20MB | 中文 OCR 识别包 |
| `english_g2.zip` | ~14MB | 英文 OCR 识别包 |

## 最佳实践

1. **仅在必要时使用 LFS** - 不是所有大文件都需要 LFS
2. **定期清理** - 使用 `git lfs prune` 清理旧版本
3. **避免提交临时文件** - 使用 `.gitignore` 排除
4. **文档说明** - 在 README 中说明 LFS 配置