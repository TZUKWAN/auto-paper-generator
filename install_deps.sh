#!/bin/bash
# 安装wxPython GUI依赖

echo "============================================================"
echo "商业计划书自动化系统 - 依赖安装脚本"
echo "============================================================"
echo ""

echo "正在检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "[错误] 未找到Python，请先安装Python 3.8+"
    exit 1
fi

echo ""
echo "正在安装依赖包..."
echo ""

# 升级pip
echo "[1/2] 升级pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "[2/2] 安装项目依赖..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 依赖安装失败，请检查网络连接或手动安装"
    exit 1
fi

echo ""
echo "============================================================"
echo "依赖安装完成！"
echo "============================================================"
echo ""
echo "运行方式:"
echo "  python3 src/main.py"
echo ""
