#!/bin/bash
# 上传 APK 到 GitHub Releases

REPO="SxLiuYu/openclaw-clients"
APK_PATH="/home/admin/.openclaw/workspace/openclaw-clients/android/app/build/outputs/apk/debug/app-debug.apk"
TAG="v2026.03.03"
TOKEN="$1"

if [ -z "$TOKEN" ]; then
    echo "用法：$0 <GitHub Token>"
    exit 1
fi

echo "📦 创建 Release..."

# 创建 Release
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/releases \
  -d "{
    \"tag_name\": \"$TAG\",
    \"name\": \"2026-03-03 设备管理版本\",
    \"body\": \"## 新功能\\n\\n- ✅ 设备管理界面\\n- ✅ 飞书 Webhook 集成\\n- ✅ 修复闪退问题\\n\\n## 安装\\n下载 app-debug.apk 并安装\",
    \"draft\": false,
    \"prerelease\": false
  }")

RELEASE_ID=$(echo $RESPONSE | grep -o '"id": [0-9]*' | head -1 | grep -o '[0-9]*')

if [ -z "$RELEASE_ID" ]; then
    echo "❌ 创建 Release 失败"
    echo $RESPONSE
    exit 1
fi

echo "✅ Release 创建成功 (ID: $RELEASE_ID)"

echo "📤 上传 APK..."

# 上传 APK
curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/vnd.android.package-archive" \
  --data-binary @"$APK_PATH" \
  "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=app-debug.apk"

echo ""
echo "✅ 上传完成！"
echo "📥 下载地址：https://github.com/$REPO/releases/download/$TAG/app-debug.apk"
