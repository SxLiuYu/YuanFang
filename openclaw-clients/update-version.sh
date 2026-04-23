#!/bin/bash
# 快速更新版本号脚本
# 用法：./update-version.sh v2026.03.03 202603031

VERSION=$1
CODE=$2

if [ -z "$VERSION" ] || [ -z "$CODE" ]; then
    echo "❌ 用法：$0 <versionName> <versionCode>"
    echo "示例：$0 v2026.03.03 202603031"
    echo ""
    echo "当前版本信息："
    grep -E "versionCode|versionName" android/app/build.gradle | head -2
    exit 1
fi

echo "📝 更新版本信息..."
echo "   versionName: $VERSION"
echo "   versionCode: $CODE"

# 更新 build.gradle
sed -i "s/versionCode [0-9]*/versionCode $CODE/" android/app/build.gradle
sed -i "s/versionName \"[^\"]*\"/versionName \"$VERSION\"/" android/app/build.gradle

# 显示更新结果
echo ""
echo "✅ 更新后："
grep -E "versionCode|versionName" android/app/build.gradle | head -2

# 提交
echo ""
echo "📦 提交代码..."
git add android/app/build.gradle
git commit -m "release: $VERSION"
git tag $VERSION

echo ""
echo "🚀 推送到 GitHub..."
git push origin main
git push origin $VERSION

echo ""
echo "✅ 版本已更新到 $VERSION"
echo "📥 GitHub Actions 将自动构建 APK"
echo "🔗 下载地址：https://github.com/SxLiuYu/openclaw-clients/releases/download/$VERSION/app-debug.apk"
