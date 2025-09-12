#!/bin/bash

# Docker 启动脚本
set -e

echo "=== U2 Magic Catcher 启动脚本 ==="
echo "时间: $(date)"
echo "用户: $(whoami)"
echo "工作目录: $(pwd)"

# 检查必要的环境变量
if [ -z "$U2_COOKIES" ] && [ -z "$U2_API_TOKEN" ]; then
    echo "警告: 必须设置 U2_COOKIES 或 U2_API_TOKEN 中的至少一种认证方式"
    echo "API 模式: 设置 U2_API_TOKEN 环境变量"
    echo "Cookie 模式: 设置 U2_COOKIES 环境变量"
fi

# 显示配置信息
echo "=== 当前配置 ==="
echo "认证方式: $([ -n "$U2_API_TOKEN" ] && echo "API Token" || echo "Cookie")"
echo "检查间隔: ${U2_INTERVAL:-120} 秒"
echo "内存限制: ${U2_MEMORY_LIMIT_MB:-512} MB"
echo "运行模式: ${U2_RUN_CRONTAB:-false}"
echo "autobrr_lb 模式: ${U2_USE_AUTOBRR_LB:-true}"
echo "健康检查端口: ${U2_HEALTH_CHECK_PORT:-8080}"
echo "=================="

# 修复目录权限（因为卷挂载可能覆盖了权限）
echo "修复目录权限..."
if [ -d "/app/data" ]; then
    # 确保 data 目录及其子目录存在且可写
    mkdir -p /app/data/backup /app/data/watch
    # 尝试修复权限（如果可能的话）
    chmod 755 /app/data /app/data/backup /app/data/watch 2>/dev/null || true
fi

if [ -d "/app/logs" ]; then
    # 确保 logs 目录可写
    chmod 755 /app/logs 2>/dev/null || true
fi

# 验证目录权限
echo "验证目录权限..."
if [ -w "/app/data" ] && [ -w "/app/logs" ]; then
    echo "✅ 目录权限正常"
else
    echo "❌ 目录权限异常"
    echo "目录信息:"
    ls -la /app/ | grep -E "(data|logs)"
    echo ""
    echo "尝试使用临时目录..."
    # 如果无法写入，使用临时目录
    export U2_LOG_PATH="/tmp/catch_magic.log"
    export U2_DATA_PATH="/tmp/catch_magic.data.txt"
    echo "使用临时目录: $U2_LOG_PATH"
fi

echo "=== 启动 U2 Magic Catcher ==="

# 执行传入的命令
exec "$@"