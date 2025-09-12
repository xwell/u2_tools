# Docker 配置说明

## 环境变量配置方式

Docker Compose 支持多种环境变量配置方式，本项目使用 `.env` 文件方式，这是最推荐的做法。

### 1. 使用 .env 文件（推荐）

```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件
nano .env
```

Docker Compose 会自动读取 `.env` 文件中的所有环境变量。

### 2. 直接在 docker compose.yml 中配置（不推荐）

```yaml
environment:
  - U2_API_TOKEN=your_token
  - U2_INTERVAL=120
```

这种方式不推荐，因为：
- 配置硬编码在文件中
- 不便于版本控制
- 难以管理敏感信息

### 3. 使用环境变量文件

```yaml
env_file:
  - .env
  - .env.local  # 本地覆盖配置
```

## 配置优先级

Docker Compose 的环境变量优先级（从高到低）：

1. **Shell 环境变量**
   ```bash
   export U2_API_TOKEN=your_token
   docker compose up
   ```

2. **docker compose.yml 中的 environment**
   ```yaml
   environment:
     - U2_API_TOKEN=your_token
   ```

3. **env_file 指定的文件**
   ```yaml
   env_file:
     - .env
   ```

4. **默认值**

## 最佳实践

### 1. 使用 .env 文件

```bash
# 项目根目录
.env                    # 主配置文件
.env.example           # 配置模板
.env.local            # 本地覆盖（不提交到版本控制）
```

### 2. 配置管理

```bash
# 复制模板
cp env.example .env

# 编辑配置
nano .env

# 验证配置
docker compose config
```

### 3. 安全考虑

```bash
# .env 文件包含敏感信息，不要提交到版本控制
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# 只提交模板文件
git add env.example
```

## 配置示例

### 基础配置

```bash
# .env 文件内容
U2_API_TOKEN=your_api_token_here
U2_UID=50096
U2_INTERVAL=120
U2_RUN_CRONTAB=false
```

### 完整配置

```bash
# 认证配置
U2_API_TOKEN=your_api_token_here
U2_UID=50096

# 基础配置
U2_INTERVAL=120
U2_RUN_CRONTAB=false

# 内存配置
U2_MEMORY_LIMIT_MB=512
U2_MEMORY_CHECK_INTERVAL=300

# 下载策略
U2_DOWNLOAD_NON_FREE=false
U2_MIN_DAY=7
U2_DOWNLOAD_OLD=true
U2_DOWNLOAD_NEW=false

# autobrr_lb 配置
U2_USE_AUTOBRR_LB=true
U2_AUTOBRR_LB_URL=http://autobrr-lb:5000
U2_AUTOBRR_LB_PATH=/webhook/secure-a8f9c2e1-4b3d-9876-abcd-ef0123456789
```

## 故障排除

### 1. 环境变量未生效

```bash
# 检查 .env 文件是否存在
ls -la .env

# 检查配置语法
docker compose config

# 查看实际环境变量
docker compose exec u2-magic-catcher env | grep U2_
```

### 2. 配置验证

```bash
# 验证 Docker Compose 配置
docker compose config

# 检查环境变量
docker compose exec u2-magic-catcher python -c "import os; print('API Token:', '已设置' if os.getenv('U2_API_TOKEN') else '未设置')"
```

### 3. 调试配置

```bash
# 查看容器环境变量
docker compose exec u2-magic-catcher env

# 查看特定变量
docker compose exec u2-magic-catcher printenv U2_API_TOKEN
```

## 多环境配置

### 开发环境

```bash
# .env.dev
U2_API_TOKEN=dev_token
U2_INTERVAL=60
U2_LOG_LEVEL=DEBUG
```

### 生产环境

```bash
# .env.prod
U2_API_TOKEN=prod_token
U2_INTERVAL=300
U2_LOG_LEVEL=INFO
```

### 使用不同环境

```bash
# 使用开发环境
docker compose --env-file .env.dev up

# 使用生产环境
docker compose --env-file .env.prod up
```
