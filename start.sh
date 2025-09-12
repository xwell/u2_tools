#!/bin/bash

# U2 Magic Catcher 启动脚本

set -e

echo "=== U2 Magic Catcher 启动脚本 ==="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "未找到 .env 文件，正在创建..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "已复制 env.example 为 .env"
        echo ""
        echo "⚠️  请编辑 .env 文件配置您的参数："
        echo "   - 设置 U2_API_TOKEN 或 U2_COOKIES"
        echo "   - 调整其他配置项（可选）"
        echo ""
        echo "编辑完成后，请重新运行此脚本"
        exit 0
    else
        echo "错误: 未找到 env.example 文件"
        exit 1
    fi
fi

# 检查必要的配置
if ! grep -q "U2_API_TOKEN=" .env && ! grep -q "U2_COOKIES=" .env; then
    echo "警告: .env 文件中未设置认证方式"
    echo "请设置 U2_API_TOKEN 或 U2_COOKIES 中的至少一种"
    echo "编辑 .env 文件后重新运行此脚本"
    exit 1
fi

# 准备目录和权限
echo "准备目录和权限..."
mkdir -p data/backup data/watch logs
chmod 755 data data/backup data/watch logs

# 构建并启动服务
echo "构建 Docker 镜像..."
docker compose build

echo "启动服务..."
docker compose up -d

echo "=== 服务已启动 ==="
echo "健康检查: http://localhost:8080/health"
echo "查看日志: docker compose logs -f u2-magic-catcher"
echo "停止服务: docker compose down"
echo "=================="