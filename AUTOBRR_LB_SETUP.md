# autobrr_lb 负载均衡器配置指南

## 概述

[autobrr_loadbalance](https://github.com/guowanghushifu/autobrr_loadbalance) 是一个为 qBittorrent 多实例设计的智能负载均衡器，通过 webhook 接收 autobrr 的种子添加请求，自动分配到最优实例。

## 安装步骤

### 1. 克隆并构建 autobrr_loadbalance

```bash
# 克隆项目
git clone https://github.com/guowanghushifu/autobrr_loadbalance.git
cd autobrr_loadbalance

# 构建 Docker 镜像
docker build -t qbittorrent-loadbalancer .
```

### 2. 配置 autobrr_lb

```bash
# 回到 u2_tools 目录
cd ../u2_tools

# 创建配置目录
mkdir -p autobrr-lb-config autobrr-lb-logs

# 复制配置模板
cp ../autobrr_loadbalance/config.json.example ./autobrr-lb-config/config.json
```

### 3. 编辑配置文件

编辑 `autobrr-lb-config/config.json`：

```json
{
  "qbittorrent_instances": [
    {
      "name": "qBittorrent-1",
      "host": "192.168.1.100",
      "port": 8080,
      "username": "admin",
      "password": "password123"
    },
    {
      "name": "qBittorrent-2", 
      "host": "192.168.1.101",
      "port": 8080,
      "username": "admin",
      "password": "password123"
    }
  ],
  "webhook_path": "/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789",
  "webhook_port": 5000,
  "primary_sort_key": "upload_speed",
  "max_new_tasks_per_instance": 2,
  "max_announce_retries": 30,
  "fast_announce_interval": 3,
  "connection_timeout": 6,
  "debug_add_stopped": false,
  "fast_announce_category_blacklist": []
}
```

### 4. 启动 autobrr_lb 服务

```bash
# 启动 autobrr_lb 服务（使用 profile）
docker compose --profile autobrr up -d

# 或者启动所有服务
docker compose up -d
```

### 5. 配置 U2 Magic Catcher

在 `.env` 文件中设置：

```bash
# 启用 autobrr_lb 模式
U2_USE_AUTOBRR_LB=true

# autobrr_lb 地址（使用容器名）
U2_AUTOBRR_LB_URL=http://qbt-loadbalancer:5000

# webhook 路径（与 config.json 中的 webhook_path 一致）
U2_AUTOBRR_LB_PATH=/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789

# 种子分类
U2_AUTOBRR_LB_CATEGORY=U2-Magic

# 推送失败时回退到本地下载
U2_FALLBACK_TO_LOCAL=true
```

## 配置说明

### 必需配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `qbittorrent_instances` | qBittorrent 实例列表 | 见配置示例 |
| `webhook_path` | Webhook 访问路径（**必须随机化**） | `/webhook/secure-random-string` |

### 常用配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `webhook_port` | 5000 | Webhook 监听端口 |
| `primary_sort_key` | `upload_speed` | 负载均衡策略 |
| `max_new_tasks_per_instance` | 2 | 单实例单轮最大新任务数 |
| `max_announce_retries` | 30 | 种子最大汇报重试次数 |
| `fast_announce_interval` | 3 | 快速检查间隔（秒） |
| `connection_timeout` | 6 | 连接超时时间（秒） |

### 负载均衡策略

- `upload_speed`: 按上传速度排序（推荐）
- `download_speed`: 按下载速度排序
- `active_downloads`: 按活跃下载数排序

## 安全说明

⚠️ **重要**: `webhook_path` 必须设置为长且随机的字符串，这是应用安全的核心。

- ❌ 错误: `/webhook`, `/autobrr`
- ✅ 正确: `/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789`

## 管理命令

```bash
# 启动 autobrr_lb 服务
docker compose --profile autobrr up -d

# 停止 autobrr_lb 服务
docker compose --profile autobrr down

# 查看 autobrr_lb 日志
docker compose logs -f qbt-loadbalancer

# 重启 autobrr_lb 服务
docker compose restart qbt-loadbalancer
```

## 健康检查

```bash
# 检查 autobrr_lb 健康状态
curl http://localhost:5000/health

# 检查服务状态
docker compose ps qbt-loadbalancer
```

## 故障排除

### 1. 连接失败

```bash
# 检查 qBittorrent Web UI 设置
# 确保启用了 Web UI 并设置了正确的端口

# 测试网络连通性
docker compose exec qbt-loadbalancer ping 192.168.1.100
```

### 2. Webhook 无响应

```bash
# 确认 webhook_path 配置正确
# 检查防火墙设置
# 验证端口映射

# 查看日志
docker compose logs qbt-loadbalancer
```

### 3. 调试模式

在 `config.json` 中设置：

```json
{
  "debug_add_stopped": true
}
```

这将暂停新种子添加，便于调试。

## 与 U2 Magic Catcher 集成

1. **配置 U2 Magic Catcher** 使用 autobrr_lb 模式
2. **设置正确的 webhook 路径** 确保两端配置一致
3. **启用回退机制** 当 autobrr_lb 不可用时自动回退到本地下载
4. **监控日志** 确保种子正确推送到负载均衡器

## 参考资料

- [autobrr_loadbalance 项目](https://github.com/guowanghushifu/autobrr_loadbalance)
- [配置示例](https://github.com/guowanghushifu/autobrr_loadbalance/blob/main/config.json.example)
