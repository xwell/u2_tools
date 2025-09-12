# Docker 资源限制配置说明

## 概述

Docker 支持多种资源限制配置方式，但不同环境下的配置语法不同。

## 配置方式对比

### 1. 单机 Docker Compose（推荐）

适用于 `docker compose up -d` 命令：

```yaml
services:
  u2-magic-catcher:
    # 内存限制
    mem_limit: 1g              # 最大内存 1GB
    memswap_limit: 1g          # 交换内存限制 1GB
    mem_reservation: 256m      # 内存预留 256MB
    
    # CPU 限制
    cpus: 0.5                  # 最多使用 0.5 个 CPU 核心
```

### 2. Docker Swarm 模式

适用于 `docker stack deploy` 命令：

```yaml
services:
  u2-magic-catcher:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.1'
```

### 3. 直接 Docker 运行

```bash
docker run -d \
  --memory=1g \
  --memory-swap=1g \
  --cpus=0.5 \
  --memory-reservation=256m \
  u2-magic-catcher
```

## 当前项目配置

项目使用单机 Docker Compose 配置：

```yaml
# docker-compose.yml
services:
  u2-magic-catcher:
    mem_limit: 1g              # 最大内存 1GB
    memswap_limit: 1g          # 交换内存限制 1GB
    cpus: 0.5                  # 最多使用 0.5 个 CPU 核心
    mem_reservation: 256m      # 内存预留 256MB
```

## 资源限制说明

### 内存限制

| 参数 | 说明 | 示例 |
|------|------|------|
| `mem_limit` | 容器最大可用内存 | `1g`, `512m` |
| `memswap_limit` | 交换内存限制 | `1g`, `0`（禁用交换） |
| `mem_reservation` | 内存预留（软限制） | `256m` |

### CPU 限制

| 参数 | 说明 | 示例 |
|------|------|------|
| `cpus` | CPU 核心数限制 | `0.5`, `1.0`, `2` |

## 验证资源限制

### 1. 查看容器资源使用

```bash
# 查看容器资源使用情况
docker stats u2-magic-catcher

# 查看容器详细信息
docker inspect u2-magic-catcher | grep -A 10 "Memory\|Cpu"
```

### 2. 测试内存限制

```bash
# 进入容器
docker compose exec u2-magic-catcher bash

# 查看内存限制
cat /sys/fs/cgroup/memory/memory.limit_in_bytes

# 查看当前内存使用
free -h
```

### 3. 测试 CPU 限制

```bash
# 查看 CPU 限制
cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us
cat /sys/fs/cgroup/cpu/cpu.cfs_period_us
```

## 性能调优建议

### 1. 内存配置

```yaml
# 轻量级配置
mem_limit: 512m
mem_reservation: 128m

# 标准配置
mem_limit: 1g
mem_reservation: 256m

# 高性能配置
mem_limit: 2g
mem_reservation: 512m
```

### 2. CPU 配置

```yaml
# 轻量级配置
cpus: 0.25

# 标准配置
cpus: 0.5

# 高性能配置
cpus: 1.0
```

### 3. 根据实际需求调整

```bash
# 监控资源使用
docker stats --no-stream

# 根据使用情况调整配置
# 编辑 docker-compose.yml
nano docker-compose.yml

# 重启服务应用新配置
docker compose up -d
```

## 故障排除

### 1. 内存不足

```bash
# 症状：容器频繁重启
# 解决：增加内存限制
mem_limit: 2g
mem_reservation: 512m
```

### 2. CPU 使用率过高

```bash
# 症状：系统响应缓慢
# 解决：限制 CPU 使用
cpus: 0.5
```

### 3. 交换内存问题

```bash
# 症状：性能下降
# 解决：禁用交换内存
memswap_limit: 0
```

## 环境变量配置

可以通过环境变量动态配置资源限制：

```yaml
# docker-compose.yml
services:
  u2-magic-catcher:
    mem_limit: ${MEMORY_LIMIT:-1g}
    cpus: ${CPU_LIMIT:-0.5}
```

```bash
# .env 文件
MEMORY_LIMIT=2g
CPU_LIMIT=1.0
```

## 最佳实践

1. **从保守配置开始**：先设置较小的资源限制
2. **监控资源使用**：使用 `docker stats` 监控实际使用情况
3. **逐步调整**：根据实际需求逐步增加资源限制
4. **预留缓冲**：设置适当的内存预留，避免 OOM
5. **禁用交换**：对于性能敏感的应用，考虑禁用交换内存
