"""Redis 连接池封装"""
from redis.asyncio import Redis
from app.config import settings

redis_client: Redis | None = None


async def get_redis() -> Redis:
    """获取 Redis 连接"""
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
