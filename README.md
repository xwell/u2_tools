# U2 Magic Catcher

一个用于自动监控和下载 U2 网站魔法种子的 Python 脚本，支持 Docker 容器化部署和长时间运行。

## 功能特性

- 🔄 **自动监控**: 持续监控 U2 网站的魔法列表
- 🎯 **智能过滤**: 支持多种过滤条件（类型、大小、名称等）
- 📦 **Docker 支持**: 完整的容器化部署方案
- 💾 **内存优化**: 内置内存监控和垃圾回收机制
- 🏥 **健康检查**: HTTP 健康检查接口
- 📊 **状态监控**: 详细的运行状态和统计信息
- 🔧 **环境配置**: 支持环境变量配置
- 🚀 **autobrr_lb 集成**: 支持推送到 autobrr_lb 负载均衡器

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd u2_tools
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

**认证配置**（二选一）:
- `U2_API_TOKEN`: U2 API Token（推荐）
- `U2_COOKIES`: U2 网站的登录 Cookie（备选）

> **注意**: Docker Compose 会自动从 `.env` 文件读取环境变量，无需在 `docker-compose.yml` 中重复配置。

### 3. 使用 Docker 运行

```bash
# 启动服务
./start.sh

# 或者手动启动
docker compose up -d
```

### 4. 检查服务状态

```bash
# 健康检查
./health-check.sh

# 查看日志
docker compose logs -f u2-magic-catcher
```

## 配置说明

### 基础配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `U2_API_TOKEN` | - | U2 API Token（推荐） |
| `U2_COOKIES` | - | U2 网站 Cookie（备选） |
| `U2_INTERVAL` | 120 | 检查间隔（秒） |
| `U2_UID` | 50096 | 用户 ID（使用 API 时需要） |

### 下载策略

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `U2_DOWNLOAD_NON_FREE` | false | 是否下载非免费种子 |
| `U2_MIN_DAY` | 7 | 新旧种子分界线（天） |
| `U2_DOWNLOAD_OLD` | true | 是否下载旧种子 |
| `U2_DOWNLOAD_NEW` | false | 是否下载新种子 |
| `U2_DA_QIAO` | true | 是否启用搭桥机制 |

### 过滤配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `U2_CAT_FILTER` | - | 种子类型过滤（逗号分隔） |
| `U2_SIZE_FILTER` | [0, -1] | 大小过滤 [最小值GB, 最大值GB] |
| `U2_NAME_FILTER` | - | 名称过滤（逗号分隔） |

### autobrr_lb 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `U2_USE_AUTOBRR_LB` | true | 是否使用 autobrr_lb |
| `U2_AUTOBRR_LB_URL` | http://autobrr-lb:5000 | autobrr_lb 地址 |
| `U2_AUTOBRR_LB_PATH` | /webhook/... | webhook 路径 |
| `U2_AUTOBRR_LB_CATEGORY` | U2-Magic | 种子分类 |

## 运行模式

### 长时间运行模式（推荐）

```bash
# 设置环境变量
export U2_RUN_CRONTAB=false

# 启动服务
docker compose up -d
```

### 定时任务模式

```bash
# 设置环境变量
export U2_RUN_CRONTAB=true
export U2_RUN_TIMES=1

# 启动服务
docker compose up -d
```

## 健康检查

服务提供 HTTP 健康检查接口：

```bash
# 检查服务状态
curl http://localhost:8080/health

# 使用健康检查脚本
./health-check.sh
```

健康检查返回的 JSON 格式：

```json
{
  "status": "healthy",
  "last_check": 1640995200.0,
  "memory_usage_mb": 128.5,
  "total_checks": 100,
  "successful_downloads": 15,
  "failed_downloads": 2,
  "uptime": 3600.0
}
```

## 监控和日志

### 查看日志

```bash
# 实时查看日志
docker compose logs -f u2-magic-catcher

# 查看最近的日志
docker compose logs --tail=100 u2-magic-catcher
```

### 日志文件

日志文件位置：`./logs/catch_magic.log`

- 自动轮转：10MB
- 保留时间：7天
- 自动压缩：zip格式

## 内存管理

脚本内置内存监控和优化机制：

- **内存限制**: 默认 512MB
- **自动检查**: 每5分钟检查一次内存使用
- **垃圾回收**: 内存使用率超过80%时自动执行
- **优雅退出**: 内存超限时自动停止

## 故障排除

### 常见问题

1. **权限问题**
   ```
   错误: Permission denied
   解决: 运行目录准备脚本
   ```
   ```bash
   # Linux/Mac
   ./prepare-dirs.sh
   
   # Windows
   prepare-dirs.bat
   ```

2. **Cookie 无效**
   ```
   错误: 无法访问 U2 网站
   解决: 检查 U2_COOKIES 环境变量是否正确
   ```

3. **内存不足**
   ```
   错误: 内存使用超过限制
   解决: 增加 U2_MEMORY_LIMIT_MB 或优化过滤条件
   ```

4. **网络超时**
   ```
   错误: 请求超时
   解决: 增加 U2_REQUEST_TIMEOUT 或检查网络连接
   ```

### 调试模式

```bash
# 启用调试日志
export U2_LOG_LEVEL=DEBUG

# 重新启动服务
docker compose restart u2-magic-catcher
```

## 开发

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export U2_COOKIES='{"nexusphp_u2": "your_cookie"}'

# 运行脚本
python catch_magic.py
```

### 构建镜像

```bash
# 构建镜像
docker build -t u2-magic-catcher .

# 运行容器
docker run -d --name u2-magic-catcher \
  -e U2_COOKIES='{"nexusphp_u2": "your_cookie"}' \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  u2-magic-catcher
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v2.0.0
- ✅ 添加 Docker 支持
- ✅ 优化内存管理
- ✅ 添加健康检查
- ✅ 支持环境变量配置
- ✅ 改进错误处理
- ✅ 添加 autobrr_lb 集成
- ✅ 修复权限问题