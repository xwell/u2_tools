@echo off
REM 目录准备脚本 (Windows)

echo === 准备目录和权限 ===

REM 创建宿主机目录
echo 创建宿主机目录...
if not exist "data" mkdir data
if not exist "data\backup" mkdir data\backup
if not exist "data\watch" mkdir data\watch
if not exist "logs" mkdir logs

echo ✅ 目录创建完成

REM 显示目录信息
echo.
echo 目录结构:
dir data /b 2>nul
dir logs /b 2>nul

echo.
echo === 目录准备完成 ===
echo 现在可以运行: start.bat 或 ./start.sh
pause
