#!/bin/bash

# qBittorrent 负载均衡器快速设置脚本

set -e

echo "=== qBittorrent 负载均衡器快速设置脚本 ==="

# 检查是否已构建镜像
if ! docker images | grep -q "qbittorrent-loadbalancer"; then
    echo "❌ 未找到 qbittorrent-loadbalancer 镜像"
    echo "请先构建镜像："
    echo "  git clone https://github.com/xwell/autobrr_loadbalance.git"
    echo "  cd autobrr_loadbalance && docker build -t qbittorrent-loadbalancer ."
    exit 1
fi

echo "✅ 找到 qbittorrent-loadbalancer 镜像"

# 创建配置目录
echo "创建配置目录..."
mkdir -p qbt-loadbalancer-config qbt-loadbalancer-logs

# 检查配置文件是否存在
if [ ! -f "qbt-loadbalancer-config/config.json" ]; then
    echo "创建配置文件..."
    cat > qbt-loadbalancer-config/config.json << 'EOF'
{
    "qbittorrent_instances": [
        {
            "name": "qBittorrent-1",
            "url": "http://192.168.1.100:8080",
            "username": "admin",
            "password": "your_password",
            "traffic_check_url": "",
            "traffic_limit": 0,
            "reserved_space": 21504
        },
        {
            "name": "qBittorrent-2",
            "url": "http://192.168.1.101:8080",
            "username": "admin",
            "password": "your_password",
            "traffic_check_url": "",
            "traffic_limit": 0,
            "reserved_space": 21504
        }
    ],
    "webhook_port": 5000,
    "webhook_path": "/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789",
    "max_new_tasks_per_instance": 2,
    "max_announce_retries": 30,
    "fast_announce_interval": 3,
    "reconnect_interval": 120,
    "max_reconnect_attempts": 1,
    "connection_timeout": 6,
    "primary_sort_key": "upload_speed",
    "log_dir": "./logs",
    "debug_add_stopped": false,
    "fast_announce_category_blacklist": [
        "redacted",
        "xxxxxxxx"
    ],
    "_comment_traffic": "注意，traffic_check_url需要配合其他工具使用，默认留空，不检查流量；traffic_limit 和 reserved_space 单位为MB",
    "_comment_blacklist": "fast_announce_category_blacklist: 快速汇报分类黑名单，处于此列表中的种子分类不会触发快速汇报功能"
}
EOF
    echo "✅ 配置文件已创建: qbt-loadbalancer-config/config.json"
    echo "⚠️  请编辑配置文件，设置您的 qBittorrent 实例信息"
else
    echo "✅ 配置文件已存在: qbt-loadbalancer-config/config.json"
fi

# 设置目录权限
echo "设置目录权限..."
chmod 755 qbt-loadbalancer-config qbt-loadbalancer-logs
chmod 644 qbt-loadbalancer-config/config.json

# 显示配置信息
echo ""
echo "=== 配置信息 ==="
echo "配置文件: qbt-loadbalancer-config/config.json"
echo "日志目录: qbt-loadbalancer-logs/"
echo "Webhook 端口: 5000"
echo "健康检查: http://localhost:5000/health"
echo "================"

echo ""
echo "=== 下一步操作 ==="
echo "1. 编辑配置文件: nano qbt-loadbalancer-config/config.json"
echo "2. 启动服务: docker compose --profile qbt-lb up -d"
echo "3. 查看日志: docker compose --profile qbt-lb logs -f qbt-loadbalancer"
echo "4. 健康检查: curl http://localhost:5000/health"
echo "================"