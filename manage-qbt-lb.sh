#!/bin/bash

# qBittorrent 负载均衡器管理脚本

set -e

case "$1" in
    "start")
        echo "启动 qBittorrent 负载均衡器服务..."
        docker compose --profile qbt-lb up -d qbt-loadbalancer
        echo "✅ qBittorrent 负载均衡器服务已启动"
        ;;
    "stop")
        echo "停止 qBittorrent 负载均衡器服务..."
        docker compose --profile qbt-lb down qbt-loadbalancer
        echo "✅ qBittorrent 负载均衡器服务已停止"
        ;;
    "restart")
        echo "重启 qBittorrent 负载均衡器服务..."
        docker compose --profile qbt-lb restart qbt-loadbalancer
        echo "✅ qBittorrent 负载均衡器服务已重启"
        ;;
    "logs")
        echo "查看 qBittorrent 负载均衡器日志..."
        docker compose --profile qbt-lb logs -f qbt-loadbalancer
        ;;
    "status")
        echo "查看 qBittorrent 负载均衡器状态..."
        docker compose --profile qbt-lb ps qbt-loadbalancer
        ;;
    "health")
        echo "检查 qBittorrent 负载均衡器健康状态..."
        curl -f http://localhost:5000/health || echo "❌ 健康检查失败"
        ;;
    "all")
        echo "启动所有服务（包括 qBittorrent 负载均衡器）..."
        docker compose --profile qbt-lb up -d
        echo "✅ 所有服务已启动"
        ;;
    *)
        echo "qBittorrent 负载均衡器管理脚本"
        echo ""
        echo "用法: $0 {start|stop|restart|logs|status|health|all}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动 qBittorrent 负载均衡器服务"
        echo "  stop    - 停止 qBittorrent 负载均衡器服务"
        echo "  restart - 重启 qBittorrent 负载均衡器服务"
        echo "  logs    - 查看 qBittorrent 负载均衡器日志"
        echo "  status  - 查看 qBittorrent 负载均衡器状态"
        echo "  health  - 检查 qBittorrent 负载均衡器健康状态"
        echo "  all     - 启动所有服务（包括 qBittorrent 负载均衡器）"
        echo ""
        echo "示例:"
        echo "  $0 start    # 启动 qBittorrent 负载均衡器"
        echo "  $0 logs     # 查看日志"
        echo "  $0 health   # 健康检查"
        ;;
esac
