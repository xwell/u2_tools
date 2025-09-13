# 使用说明

## 快速开始

### 1. 配置认证方式

**重要**: Cookie 是**必需的**，因为获取种子下载链接需要 Cookie 认证。API Token 是可选的，用于获取魔法信息。

#### 必需: Cookie 配置

1. 登录 U2 网站
2. 打开浏览器开发者工具（F12）
3. 在 Network 标签页中找到任意请求
4. 复制完整的 Cookie 字符串

**格式1: 浏览器 Cookie 字符串格式（推荐）**
```bash
U2_COOKIES=PHPSESSID=your_phpsessid; nexusphp_u2=your_nexusphp_u2_cookie
```

**格式2: JSON 格式**
```bash
U2_COOKIES={"nexusphp_u2": "你的cookie值"}
```

#### 可选: API Token 配置

1. 访问 U2 API 获取 Token
2. 在 `.env` 文件中设置：
```bash
U2_API_TOKEN=your_api_token_here
U2_UID=your_user_id
```

> **说明**: 如果同时设置了 API Token 和 Cookie，将使用 API 获取魔法信息，Cookie 用于种子下载。

### 2. 配置环境变量

```bash
# 复制配置文件
cp env.example .env

# 编辑配置文件
nano .env
```

> **重要**: Docker Compose 会自动从 `.env` 文件读取所有环境变量，这是推荐的配置方式。

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
./start.sh

# 或手动启动
docker compose up -d
```

### 4. 检查运行状态

```bash
# 健康检查
./health-check.sh

# 查看日志
docker compose logs -f u2-magic-catcher
```

## 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f u2-magic-catcher

# 查看服务状态
docker compose ps

# 进入容器
docker compose exec u2-magic-catcher bash
```

## 配置示例

### 基础配置
```bash
# 检查间隔 2 分钟
U2_INTERVAL=120

# 只下载免费种子
U2_DOWNLOAD_NON_FREE=false

# 启用搭桥机制
U2_DA_QIAO=true
```

### 过滤配置
```bash
# 只下载 BDMV 和 Lossless Music 类型
U2_CAT_FILTER=BDMV,Lossless Music

# 文件大小限制 1GB 到 50GB
U2_SIZE_FILTER=[1, 50]

# 排除包含 BDRip 的种子
U2_NAME_FILTER=BDRip
```

### autobrr_lb 配置
```bash
# 启用 autobrr_lb 推送
U2_USE_AUTOBRR_LB=true

# autobrr_lb 地址
U2_AUTOBRR_LB_URL=http://qbt-loadbalancer:5000

# 推送失败时回退到本地下载
U2_FALLBACK_TO_LOCAL=true

# 高级配置（可选）
# 下载限速，支持单位：K, KB, KiB, M, MB, MiB, G, GB, GiB /s
U2_AUTOBRR_LB_DL_LIMIT=5MB/s

# 上传限速
U2_AUTOBRR_LB_UP_LIMIT=1MB/s

# 保存路径
U2_AUTOBRR_LB_SAVEPATH=/downloads/TV
```

## 监控和调试

### 健康检查
访问 `http://localhost:8080/health` 查看服务状态

### 日志查看
```bash
# 实时查看日志
docker compose logs -f u2-magic-catcher

# 查看错误日志
docker compose logs u2-magic-catcher | grep ERROR

# 查看下载记录
docker compose logs u2-magic-catcher | grep "下载种子"
```

### 性能监控
```bash
# 查看容器资源使用
docker stats u2-magic-catcher

# 查看内存使用
docker compose exec u2-magic-catcher python -c "import psutil; print(f'内存使用: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB')"
```

## 故障排除

### 1. 认证问题
```bash
# 检查 Cookie 是否正确设置（必需）
docker compose exec u2-magic-catcher python -c "import os; print('Cookie:', '已设置' if os.getenv('U2_COOKIES') else '未设置')"

# 检查 API Token 是否正确设置（可选）
docker compose exec u2-magic-catcher python -c "import os; print('API Token:', '已设置' if os.getenv('U2_API_TOKEN') else '未设置')"
```

**常见问题**：
- 如果提示 "缺少必要的 Cookie 配置"，请确保设置了 `U2_COOKIES` 环境变量
- Cookie 格式错误：请使用 `PHPSESSID=aaa; nexusphp_u2=bbb` 或 `{"nexusphp_u2": "bbb"}` 格式

### 2. 网络问题
```bash
# 测试网络连接
docker compose exec u2-magic-catcher curl -I https://u2.dmhy.org
```

### 3. 权限问题
```bash
# 检查目录权限
ls -la data/
ls -la logs/
```

### 4. 内存问题
```bash
# 查看内存使用情况
docker compose exec u2-magic-catcher python -c "import psutil; print(psutil.virtual_memory())"
```

## 高级配置

### 使用代理
```bash
U2_PROXIES={"http": "http://proxy:8080", "https": "http://proxy:8080"}
```

### 自定义路径
```bash
U2_BK_DIR=/custom/backup/path
U2_WT_DIR=/custom/watch/path
U2_LOG_PATH=/custom/log/path
```

### 内存优化
```bash
# 降低内存限制
U2_MEMORY_LIMIT_MB=256

# 增加检查间隔
U2_MEMORY_CHECK_INTERVAL=600
```
