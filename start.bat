@echo off
chcp 65001 >nul
title YGOMaker 制卡器 - 一键启动

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║        🃏  YGOMaker 游戏王制卡器          ║
echo   ║          一键启动脚本 v1.0                ║
echo   ╚══════════════════════════════════════════╝
echo.
echo   [说明] 首次启动可能需要安装依赖，请耐心等待。
echo.

REM ============================================
REM 1. 检查 Python
REM ============================================
echo   [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)
echo          Python 已就绪

REM ============================================
REM 2. 安装/检查 Python 后端依赖
REM ============================================
echo   [2/4] 检查后端依赖...
if not exist "ygmaker-server\__deps_installed__" (
    echo         首次启动，正在安装后端依赖...
    pip install -r ygmaker-server\requirements.txt -q
    if %errorlevel% neq 0 (
        echo   [错误] 后端依赖安装失败
        pause
        exit /b 1
    )
    echo. > ygmaker-server\__deps_installed__
)
echo         后端依赖已就绪

REM ============================================
REM 3. 安装/检查前端依赖
REM ============================================
echo   [3/4] 检查前端依赖...
if not exist "yugioh-card-master\node_modules" (
    echo         首次启动，正在安装前端依赖（约15秒）...
    echo.
    cd /d "%~dp0\yugioh-card-master"
    call npm install --legacy-peer-deps --ignore-scripts
    cd /d "%~dp0"
    if %errorlevel% neq 0 (
        echo   [警告] 前端依赖安装可能未完成，请手动运行:
        echo         cd yugioh-card-master
        echo         npm install --legacy-peer-deps
    )
)
echo         前端依赖已就绪

REM ============================================
REM 4. 启动服务
REM ============================================
echo   [4/4] 启动制卡器服务...
echo.
echo   ┌─────────────────────────────────────────┐
echo   │  YGOMaker v2.0                            │
echo   │  打开浏览器访问:  http://localhost:8848    │
echo   │  关闭此窗口即可停止服务                   │
echo   └─────────────────────────────────────────┘
echo.

REM 启动后端 (自带前端静态文件)
start "YGOMaker" cmd /c "cd /d %~dp0 && python ygmaker-server\server.py"

echo   正在等待服务就绪...
timeout /t 3 /nobreak >nul

echo.
echo   启动完成！浏览器将自动打开...
timeout /t 2 /nobreak >nul
start http://localhost:8848

echo.
echo   按任意键停止服务...
pause >nul

REM 清理
taskkill /FI "WINDOWTITLE eq YGOMaker*" /T /F >nul 2>&1
echo   服务已停止。
