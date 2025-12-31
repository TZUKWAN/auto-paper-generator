@echo off
REM ========================================
REM AI学术助手 - 打包构建脚本
REM ========================================

echo.
echo ============================================
echo   AI学术助手 - EXE 打包工具
echo ============================================
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [1/5] 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用全局Python
)

REM 安装打包工具
echo.
echo [2/5] 安装/更新 PyInstaller...
pip install pyinstaller --upgrade -q
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败
    REM pause
    exit /b 1
)

REM 清理旧的构建文件
echo.
echo [3/5] 清理旧的构建文件...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

REM 创建资源目录（如果不存在）
if not exist "assets" mkdir assets

REM 开始构建
echo.
echo [4/5] 开始构建 EXE...
echo        这可能需要几分钟，请耐心等待...
echo.
pyinstaller build.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 构建失败！
    echo 请检查错误信息并确保所有依赖已正确安装。
    REM pause
    exit /b 1
)

REM 复制必要的运行时文件到输出目录
echo.
echo [5/5] 复制运行时文件...
xcopy /E /I /Y "templates" "dist\AI学术助手\templates" >nul 2>&1
copy /Y "config.yaml" "dist\AI学术助手\" >nul 2>&1
copy /Y ".env.example" "dist\AI学术助手\.env" >nul 2>&1

REM 创建输出和日志目录
mkdir "dist\AI学术助手\output" >nul 2>&1
mkdir "dist\AI学术助手\logs" >nul 2>&1
mkdir "dist\AI学术助手\data" >nul 2>&1

echo.
echo ============================================
echo   构建完成！
echo ============================================
echo.
echo 输出目录: dist\AI学术助手\
echo 可执行文件: dist\AI学术助手\AI学术助手.exe
echo.
echo 您可以将整个 "AI学术助手" 文件夹复制到其他电脑运行。
echo.

REM 询问是否打开输出目录
set /p open_dir="是否打开输出目录? (Y/N): "
if /i "%open_dir%"=="Y" (
    explorer "dist\AI学术助手"
)

REM pause
