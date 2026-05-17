"""图书馆智能服务系统 — FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import init_db, engine
from app.core.redis_client import close_redis
from app.api.v1 import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动：初始化数据库表
    init_db()
    yield
    # 关闭：清理 Redis 连接
    await close_redis()
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="高校图书馆智能服务系统 — AI 智能问答、座位预约、馆藏检索",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_v1_router)


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "service": settings.APP_NAME, "version": "2.0.0"}
