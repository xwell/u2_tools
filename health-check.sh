#!/bin/bash

# U2 Magic Catcher 健康检查脚本

HEALTH_URL="http://localhost:8080/health"
TIMEOUT=10

echo "=== U2 Magic Catcher 健康检查 ==="

# 检查服务是否运行
if ! curl -s --max-time $TIMEOUT "$HEALTH_URL" > /dev/null; then
    echo "❌ 健康检查失败: 无法连接到服务"
    echo "请检查服务是否正在运行: docker compose ps"
    exit 1
fi

# 获取健康状态
HEALTH_RESPONSE=$(curl -s --max-time $TIMEOUT "$HEALTH_URL")

if [ $? -eq 0 ]; then
    echo "✅ 服务运行正常"
    echo ""
    echo "=== 健康状态详情 ==="
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    echo "=================="
    
    # 检查状态
    STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    
    if [ "$STATUS" = "healthy" ]; then
        echo "✅ 状态: 健康"
        exit 0
    elif [ "$STATUS" = "warning" ]; then
        echo "⚠️  状态: 警告"
        exit 1
    elif [ "$STATUS" = "error" ]; then
        echo "❌ 状态: 错误"
        exit 2
    else
        echo "❓ 状态: 未知"
        exit 3
    fi
else
    echo "❌ 健康检查失败: 请求超时或网络错误"
    exit 1
fi
