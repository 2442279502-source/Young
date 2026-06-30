#!/usr/bin/env bash
# ============================================================
#  Smart Safety Demo — Linux / macOS 一键启动脚本
# ============================================================

set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  Smart Safety Demo — 智慧工地安全帽检测"
echo "============================================================"
echo ""

# --- Step 1: 检查 Python ---
echo "[1/3] 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "[错误] 未检测到 Python，请先安装 Python 3.9+"
    exit 1
fi
$PYTHON --version
echo ""

# --- Step 2: 准备环境 ---
echo "[2/3] 准备虚拟环境和依赖..."
if [ ! -d "venv" ]; then
    echo "[信息] 首次运行，正在创建虚拟环境..."
    $PYTHON -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q 2>/dev/null
echo "[信息] 依赖就绪"
echo ""

# --- Step 3: 启动 ---
echo "[3/3] 启动检测系统..."
echo "============================================================"
echo "  提示: 按 'q' 键退出  绿框=SAFE  红框=UNSAFE"
echo "============================================================"
echo ""

python main.py "$@"

echo ""
echo "[信息] 程序已结束"
