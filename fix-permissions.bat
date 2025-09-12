@echo off
REM 权限修复脚本 (Windows)

echo === 修复 U2 Magic Catcher 权限问题 ===

REM 创建目录
echo 创建目录...
if not exist "data" mkdir data
if not exist "data\backup" mkdir data\backup
if not exist "data\watch" mkdir data\watch
if not exist "logs" mkdir logs

echo ✅ 目录创建完成

REM 显示结果
echo.
echo 目录结构:
dir data /b 2>nul
dir logs /b 2>nul

echo.
echo === 权限修复完成 ===
echo 现在可以运行: start.bat 或 ./start.sh
pause
