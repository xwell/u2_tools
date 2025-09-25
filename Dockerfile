# 使用 Python 3.11 官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# 安装系统依赖（包含 gosu 用于降权运行）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY catch_magic.py .
COPY docker-entrypoint.sh .

# 创建非 root 用户（默认 uid/gid 为 1000，可在入口脚本中动态修改）
RUN useradd -m -u 1000 u2user

# 创建必要的目录并设置权限
RUN mkdir -p /app/data/backup /app/data/watch /app/logs && \
    chown -R u2user:u2user /app && \
    chmod -R 755 /app

# 设置脚本权限
RUN chmod +x docker-entrypoint.sh

# 以 root 运行，入口脚本负责修复权限并降权
# USER u2user

# 暴露健康检查端口
EXPOSE 8080

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# 设置入口点
ENTRYPOINT ["./docker-entrypoint.sh"]

# 默认命令
CMD ["python", "catch_magic.py"]