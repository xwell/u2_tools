#!/bin/bash

# 权限修复脚本

echo "=== 修复 U2 Magic Catcher 权限问题 ==="

# 获取当前用户的 UID 和 GID
USER_ID=$(id -u)
GROUP_ID=$(id -g)

echo "当前用户: $(whoami) (UID: $USER_ID, GID: $GROUP_ID)"
echo "容器用户: u2user (UID: 1000, GID: 1000)"

# 创建目录
echo "创建目录..."
mkdir -p data/backup data/watch logs

# 设置权限
echo "设置目录权限..."
chmod 755 data data/backup data/watch logs

# 设置所有者
echo "设置目录所有者..."
if [ "$USER_ID" = "0" ]; then
    echo "以 root 用户运行，设置目录所有者为 1000:1000"
    chown -R 1000:1000 data logs
else
    echo "设置目录所有者为当前用户"
    chown -R $USER_ID:$GROUP_ID data logs
fi

# 显示结果
echo ""
echo "目录权限信息:"
ls -la | grep -E "(data|logs)"
echo ""
ls -la data/ 2>/dev/null || echo "data 目录不存在"
ls -la logs/ 2>/dev/null || echo "logs 目录不存在"

echo ""
echo "=== 权限修复完成 ==="
echo "现在可以运行: ./start.sh"
