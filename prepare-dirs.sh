#!/bin/bash

# 目录准备脚本
echo "=== 准备目录和权限 ==="

# 创建宿主机目录
echo "创建宿主机目录..."
mkdir -p data/backup data/watch logs

# 设置目录权限
echo "设置目录权限..."
chmod 755 data data/backup data/watch logs

# 检查操作系统类型
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到 Linux 系统，设置用户权限..."
    # 获取当前用户的 UID 和 GID
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)
    
    echo "当前用户: $(whoami) (UID: $USER_ID, GID: $GROUP_ID)"
    
    # 设置目录所有者
    chown -R $USER_ID:$GROUP_ID data logs
    
    echo "✅ Linux 权限设置完成"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 系统..."
    echo "✅ macOS 权限设置完成"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "检测到 Windows 系统..."
    echo "✅ Windows 权限设置完成"
else
    echo "未知操作系统: $OSTYPE"
    echo "✅ 使用默认权限设置"
fi

# 显示目录信息
echo ""
echo "目录结构:"
ls -la data/ logs/ 2>/dev/null || echo "目录创建中..."

echo ""
echo "=== 目录准备完成 ==="
echo "现在可以运行: ./start.sh"
