# 版本管理规范

## 版本号格式

```
vYYYY.MM.DD-N
```

- `YYYY` - 年份
- `MM` - 月份
- `DD` - 日期
- `N` - 当日第几次发布（可选，从 1 开始）

## versionCode 规则

```
versionCode = YYYYMMDDN
```

示例：
- 2026-03-03 第 1 次发布：`202603031`
- 2026-03-03 第 2 次发布：`202603032`
- 2026-03-04 第 1 次发布：`202603041`

## versionName 规则

```
versionName = "vYYYY.MM.DD-N"
```

示例：
- 2026-03-03 第 1 次发布：`"v2026.03.03"`
- 2026-03-03 第 2 次发布：`"v2026.03.03-2"`
- 2026-03-04 第 1 次发布：`"v2026.03.04"`

## 更新流程

### 1. 修改 build.gradle

```gradle
defaultConfig {
    versionCode 202603031
    versionName "v2026.03.03"
}
```

### 2. 更新 CHANGELOG

在 `CHANGELOG-YYYY-MM-DD.md` 中添加更新内容。

### 3. 提交代码

```bash
git add -A
git commit -m "release: v2026.03.03 - 功能描述"
git push
```

### 4. 创建 Git Tag

```bash
git tag v2026.03.03
git push origin v2026.03.03
```

### 5. GitHub Actions 自动构建

- 推送 tag 后自动触发
- 自动创建 Release
- 自动上传 APK

## 版本历史

| 版本 | 日期 | versionCode | 主要更新 |
|------|------|-------------|----------|
| v2026.03.03 | 2026-03-03 | 202603031 | 设备管理 + 飞书确认 |
| v1.0 | 2026-02-27 | 1 | 初始版本 |

## 快速更新脚本

```bash
#!/bin/bash
# update-version.sh

VERSION=$1
CODE=$2

if [ -z "$VERSION" ] || [ -z "$CODE" ]; then
    echo "用法：$0 <versionName> <versionCode>"
    echo "示例：$0 v2026.03.03 202603031"
    exit 1
fi

# 更新 build.gradle
sed -i "s/versionCode [0-9]*/versionCode $CODE/" android/app/build.gradle
sed -i "s/versionName \"[^\"]*\"/versionName \"$VERSION\"/" android/app/build.gradle

# 提交
git add android/app/build.gradle
git commit -m "release: $VERSION"
git tag $VERSION
git push origin main
git push origin $VERSION

echo "✅ 版本已更新到 $VERSION"
```

## 注意事项

1. **每次发布必须更新版本号**
2. **versionCode 必须递增**
3. **同一天多次发布添加 -N 后缀**
4. **CHANGELOG 必须同步更新**
5. **Git Tag 必须与 versionName 一致**
