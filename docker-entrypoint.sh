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

# 确保目录存在
mkdir -p /app/data/backup /app/data/watch /app/logs

# 设置权限
chmod 755 /app/data/backup /app/data/watch /app/logs

echo "=== 启动 U2 Magic Catcher ==="

# 执行传入的命令
exec "$@"
