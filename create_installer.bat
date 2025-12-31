@echo off
REM ========================================
REM AI学术助手 - 创建安装包脚本
REM ========================================

echo.
echo ============================================
echo   AI学术助手 - 创建安装包
echo ============================================
echo.

REM 检查EXE是否已构建
if not exist "dist\AI学术助手\AI学术助手.exe" (
    echo [错误] 请先运行 build_exe.bat 构建EXE！
    pause
    exit /b 1
)

REM 检查Inno Setup
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo.
    echo [提示] 未检测到 Inno Setup 6
    echo.
    echo 请按以下步骤操作：
    echo   1. 访问 https://jrsoftware.org/isdl.php
    echo   2. 下载 Inno Setup 6
    echo   3. 安装到默认路径
    echo   4. 重新运行此脚本
    echo.
    echo 或者，您也可以：
    echo   - 直接将 dist\AI学术助手 文件夹打包分发
    echo.
    start https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM 创建输出目录
if not exist "installer_output" mkdir installer_output

REM 编译安装包
echo.
echo [开始] 正在创建安装包...
echo.

%ISCC% installer.iss

if errorlevel 1 (
    echo.
    echo [错误] 安装包创建失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安装包创建成功！
echo ============================================
echo.
echo 安装包位置: installer_output\AI学术助手_安装程序_v1.0.0.exe
echo.

REM 打开输出目录
explorer installer_output

pause
