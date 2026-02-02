from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from nlbone.config.settings import get_settings


class RedisClient:
    _client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            cls._client = Redis.from_url(get_settings().REDIS_URL, decode_responses=True)
        return cls._client

    @classmethod
    def close(cls):
        if cls._client is not None:
            cls._client.close()
            cls._client = None


class AsyncRedisClient:
    _client: AsyncRedis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            cls._client = AsyncRedis.from_url(get_settings().REDIS_URL, decode_responses=True)
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
