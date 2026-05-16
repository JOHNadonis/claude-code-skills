#!/bin/bash
# PPT 视频生成器 - 依赖检查和安装脚本

set -e

TOOL_DIR="/Volumes/OS/ppt-video-maker"
SKILL_DIR="$HOME/.claude/skills/ppt-video-maker"

echo "=========================================="
echo "PPT 视频生成器 - 依赖检查"
echo "=========================================="

# 检查工具目录
if [ ! -d "$TOOL_DIR" ]; then
    echo "❌ 工具目录不存在，正在创建..."
    mkdir -p "$TOOL_DIR"

    # 复制文件
    echo "📦 复制工具文件..."
    cp -r "$SKILL_DIR"/* "$TOOL_DIR/"
fi

cd "$TOOL_DIR"

# 检查 LibreOffice
echo ""
echo "[1/4] 检查 LibreOffice..."
if command -v soffice &> /dev/null; then
    echo "✅ LibreOffice 已安装"
else
    echo "❌ LibreOffice 未安装，正在安装..."
    brew install --cask libreoffice
fi

# 检查 poppler
echo ""
echo "[2/4] 检查 poppler..."
if command -v pdfinfo &> /dev/null; then
    echo "✅ poppler 已安装"
else
    echo "❌ poppler 未安装，正在安装..."
    brew install poppler
fi

# 检查 FFmpeg
echo ""
echo "[3/4] 检查 FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg 已安装"
else
    echo "❌ FFmpeg 未安装，正在安装..."
    brew install ffmpeg
fi

# 检查 Python 虚拟环境
echo ""
echo "[4/4] 检查 Python 环境..."
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 检查 Python 包
echo "📦 检查 Python 依赖..."
pip list | grep -q "openai-whisper" || pip install openai-whisper
pip list | grep -q "python-pptx" || pip install python-pptx
pip list | grep -q "pdf2image" || pip install pdf2image
pip list | grep -q "openai" || pip install openai
pip list | grep -q "pyyaml" || pip install pyyaml
pip list | grep -q "pillow" || pip install pillow

echo ""
echo "=========================================="
echo "✅ 所有依赖已就绪！"
echo "=========================================="
