@echo off
REM 安装wxPython GUI依赖

echo ============================================================
echo 商业计划书自动化系统 - 依赖安装脚本
echo ============================================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 正在安装依赖包...
echo.

REM 升级pip
echo [1/2] 升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo [2/2] 安装项目依赖...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败，请检查网络连接或手动安装
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 依赖安装完成！
echo ============================================================
echo.
echo 运行方式:
echo   python src/main.py
echo.
pause
