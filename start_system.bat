@echo off
echo ========================================================
echo       Start Automated Thesis Generation System
echo ========================================================
echo.

:: 1. 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b
)

:: 2. 检查依赖
if not exist "venv" (
    echo [INFO] Virtual environment not found, skipping check...
) else (
    call venv\Scripts\activate
)

:: 3. 启动Web服务器（后台运行）
echo [INFO] Starting Web Server...
start /b python web_api.py

:: 4. 等待服务器启动
echo [INFO] Waiting for server to initialize...
timeout /t 5 >nul

:: 5. 打开浏览器
echo [INFO] Opening Browser...
start http://localhost:5000

echo.
echo [SUCCESS] System is running!
echo Do not close this window to keep the server running.
echo.
pause
