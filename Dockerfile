# =============================================================================
# Dockerfile — 图书馆智能预约客服（FastAPI 后端）
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# 系统依赖（psycopg2、sentence-transformers 所需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令（生产：多 workers，无 reload）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
