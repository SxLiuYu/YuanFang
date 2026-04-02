FROM python:3.11-slim

LABEL maintainer="YuanFang"
LABEL description="元芳 - AI驱动的智能家居数字生命体"

WORKDIR /app

# 系统依赖（Porcupine/音频等可选，默认不含）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 数据目录（通过 volume 挂载持久化）
RUN mkdir -p /app/data/{memory_store,chat_logs,daemon_logs,dream_insights,evolution_memory,skills,rules,users,notifications}

# 环境变量默认值
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    KAIROS_ENABLED=true

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

EXPOSE ${PORT}

# 入口
CMD ["python", "main.py"]
