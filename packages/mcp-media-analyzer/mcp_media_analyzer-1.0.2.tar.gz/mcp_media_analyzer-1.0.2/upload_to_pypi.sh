#!/bin/bash
# PyPI 上傳腳本 - 從 .env 載入環境變數

set -e

echo "🔐 從 .env 載入 PyPI 認證資訊..."

# 載入上層目錄的 .env 檔案
if [ -f "../.env" ]; then
    source ../.env
    echo "✅ .env 檔案已載入"
elif [ -f "../../.env" ]; then
    source ../../.env
    echo "✅ .env 檔案已載入"
elif [ -f ".env" ]; then
    source .env
    echo "✅ .env 檔案已載入"
else
    echo "❌ 找不到 .env 檔案"
    echo ""
    echo "請確認 .env 檔案包含以下內容："
    echo "TWINE_USERNAME=__token__"
    echo "TWINE_PASSWORD=pypi-你的API-Token"
    exit 1
fi

# 檢查必要的環境變數
if [ -z "$TWINE_USERNAME" ] || [ -z "$TWINE_PASSWORD" ]; then
    echo "❌ 錯誤：環境變數未設定"
    echo ""
    echo "請在 .env 檔案中設定："
    echo "TWINE_USERNAME=__token__"
    echo "TWINE_PASSWORD=pypi-你的API-Token"
    exit 1
fi

echo "✅ 認證資訊已設定"
echo ""

# 清理舊的構建
echo "🧹 清理舊的構建..."
rm -rf dist/

# 重新構建
echo "📦 構建套件..."
uv build

echo ""
echo "📤 開始上傳到 PyPI..."
echo ""

# 匯出環境變數
export TWINE_USERNAME
export TWINE_PASSWORD

# 上傳到 PyPI
twine upload dist/*

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 發布成功！"
    echo ""
    echo "✅ 套件已發布到 PyPI："
    echo "   https://pypi.org/project/mcp-media-analyzer/"
    echo ""
    echo "📦 使用方式："
    echo "   uvx mcp-media-analyzer"
    echo ""
else
    echo ""
    echo "❌ 上傳失敗，請檢查錯誤訊息"
    exit 1
fi
