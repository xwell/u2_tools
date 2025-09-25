#!/bin/bash

# Docker 启动脚本
set -e

# 允许通过环境变量自定义运行用户/组（默认 1000:1000）
APP_UID=${APP_UID:-1000}
APP_GID=${APP_GID:-1000}

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

echo "修复目录权限..."
# 如果容器以 root 启动，则尝试对挂载目录执行 chown，避免宿主机绑定目录为 root:root 导致无法写入
if [ "$(id -u)" = "0" ]; then
    # 如果指定了 APP_GID，确保系统内存在对应组
    if ! getent group ${APP_GID} >/dev/null 2>&1; then
        groupadd -g ${APP_GID} u2group || true
    fi
    # 确保 u2user 的 uid/gid 与期望一致
    if [ "$(id -u u2user)" != "${APP_UID}" ]; then
        usermod -u ${APP_UID} u2user || true
    fi
    if [ "$(id -g u2user)" != "${APP_GID}" ]; then
        usermod -g ${APP_GID} u2user || true
    fi

    # 创建目录并修正属主
    mkdir -p /app/data/backup /app/data/watch /app/logs
    chown -R ${APP_UID}:${APP_GID} /app/data /app/logs 2>/dev/null || true
    chmod -R u+rwX,g+rwX /app/data /app/logs 2>/dev/null || true
else
    # 非 root 时尽力创建子目录与放宽权限
    mkdir -p /app/data/backup /app/data/watch /app/logs 2>/dev/null || true
    chmod -R u+rwX,g+rwX /app/data /app/logs 2>/dev/null || true
fi

# 验证目录权限
echo "验证目录权限..."
if [ -w "/app/data" ] && [ -w "/app/logs" ]; then
    echo "✅ 目录权限正常"
else
    echo "❌ 目录权限异常"
    echo "目录信息:"
    ls -ld /app/data /app/logs 2>/dev/null || true
    echo ""
    echo "尝试使用临时目录..."
    # 如果无法写入，使用临时目录
    export U2_LOG_PATH="/tmp/catch_magic.log"
    export U2_DATA_PATH="/tmp/catch_magic.data.txt"
    echo "使用临时目录: $U2_LOG_PATH"
fi

echo "=== 启动 U2 Magic Catcher ==="

# 使用 gosu 将权限降至非 root 用户后启动主进程
if [ "$(id -u)" = "0" ]; then
    exec gosu ${APP_UID}:${APP_GID} "$@"
else
    exec "$@"
fi