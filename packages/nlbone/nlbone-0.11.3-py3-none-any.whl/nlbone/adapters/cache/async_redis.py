from __future__ import annotations

import inspect
import json
import os
from typing import Any, Awaitable, Callable, Iterable, Mapping, Optional, Sequence, Union

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import LockError, RedisError

from nlbone.config.settings import get_settings
from nlbone.core.ports.cache import AsyncCachePort


def _nsver_key(ns: str) -> str:
    return f"nsver:{ns}"


def _tag_key(tag: str) -> str:
    return f"tag:{tag}"


class AsyncRedisCache(AsyncCachePort):
    def __init__(self, url: str, *, invalidate_channel: Optional[str] = None):
        self._pool = ConnectionPool.from_url(
            url,
            decode_responses=False,
            max_connections=get_settings().REDIS_MAX_CONNECTIONS,
            socket_timeout=get_settings().REDIS_TIMEOUT,
            socket_connect_timeout=get_settings().REDIS_TIMEOUT,
            health_check_interval=get_settings().REDIS_CHECK_INTERVAL,
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(), 3),
        )
        self._r = Redis(connection_pool=self._pool)
        self._ch = invalidate_channel or os.getenv("NLBONE_REDIS_INVALIDATE_CHANNEL", "cache:invalidate")

    @property
    def redis(self) -> Redis:
        return self._r

    async def close(self):
        await self._r.close()
        await self._pool.disconnect()

    async def _current_ver(self, ns: str) -> int:
        try:
            v = await self._r.get(_nsver_key(ns))
            return int(v) if v else 1
        except (ValueError, TypeError):
            return 1

    async def _full_key(self, key: str) -> str:
        try:
            ns, rest = key.split(":", 1)
        except ValueError:
            ns, rest = "app", key

        ver = await self._current_ver(ns)
        return f"{ns}:{ver}:{rest}"

    # -------- basic --------
    async def get(self, key: str) -> Optional[bytes]:
        fk = await self._full_key(key)
        return await self._r.get(fk)

    async def set(
        self, key: str, value: bytes, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        fk = await self._full_key(key)

        async with self._r.pipeline() as pipe:
            if ttl is None:
                await pipe.set(fk, value)
            else:
                await pipe.setex(fk, ttl, value)

            if tags:
                for t in tags:
                    await pipe.sadd(_tag_key(t), fk)

            await pipe.execute()

    async def delete(self, key: str) -> None:
        fk = await self._full_key(key)
        await self._r.delete(fk)

    async def exists(self, key: str) -> bool:
        fk = await self._full_key(key)
        return bool(await self._r.exists(fk))

    async def ttl(self, key: str) -> Optional[int]:
        fk = await self._full_key(key)
        t = await self._r.ttl(fk)
        return int(t) if t >= 0 else None

    # -------- multi --------

    async def mget(self, keys: Sequence[str]) -> list[Optional[bytes]]:
        if not keys:
            return []
        # Alternatively, await asyncio.gather(*[self._full_key(k) for k in keys])
        fks = [await self._full_key(k) for k in keys]
        return await self._r.mget(fks)

    async def mset(
        self, items: Mapping[str, bytes], *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        if not items:
            return

        async with self._r.pipeline() as pipe:
            for k, v in items.items():
                fk = await self._full_key(k)
                if ttl is None:
                    await pipe.set(fk, v)
                else:
                    await pipe.setex(fk, ttl, v)

                if tags:
                    for t in tags:
                        await pipe.sadd(_tag_key(t), fk)

            await pipe.execute()

    # -------- json --------

    async def get_json(self, key: str) -> Optional[Any]:
        b = await self.get(key)
        if b is None:
            return None
        try:
            return json.loads(b)
        except json.JSONDecodeError:
            return None

    async def set_json(
        self, key: str, value: Any, *, ttl: Optional[int] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        payload = json.dumps(value).encode("utf-8")
        await self.set(key, payload, ttl=ttl, tags=tags)

    # -------- invalidation --------

    async def invalidate_tags(self, tags: Iterable[str]) -> int:
        removed = 0
        async with self._r.pipeline() as pipe:
            for t in tags:
                tk = _tag_key(t)
                members = await self._r.smembers(tk)
                if members:
                    await pipe.delete(*members)
                await pipe.delete(tk)
                removed += len(members or [])
            await pipe.execute()

        try:
            payload = json.dumps({"tags": list(tags)}).encode("utf-8")
            await self._r.publish(self._ch, payload)
        except RedisError:
            pass

        return removed

    async def bump_namespace(self, namespace: str) -> int:
        v = await self._r.incr(_nsver_key(namespace))
        try:
            await self._r.publish(self._ch, json.dumps({"ns_bump": namespace}).encode("utf-8"))
        except RedisError:
            pass
        return int(v)

    async def clear_namespace(self, namespace: str) -> int:
        cnt = 0
        cursor = 0
        pattern = f"{namespace}:*"

        while True:
            cursor, keys = await self._r.scan(cursor=cursor, match=pattern, count=1000)
            if keys:
                await self._r.delete(*keys)
                cnt += len(keys)
            if cursor == 0:
                break

        try:
            await self._r.publish(self._ch, json.dumps({"ns_clear": namespace}).encode("utf-8"))
        except RedisError:
            pass

        return cnt

    # -------- dogpile-safe get_or_set --------

    async def get_or_set(
        self,
        key: str,
        producer: Callable[[], Union[bytes, str, Awaitable[Union[bytes, str]]]],
        *,
        ttl: int,
        tags: Optional[Iterable[str]] = None,
    ) -> bytes:
        fk = await self._full_key(key)

        val = await self._r.get(fk)
        if val is not None:
            return val

        lock_name = f"lock:{fk}"

        try:
            async with self._r.lock(lock_name, timeout=10, blocking_timeout=5):
                val = await self._r.get(fk)
                if val is not None:
                    return val

                if inspect.iscoroutinefunction(producer):
                    produced = await producer()
                else:
                    produced = producer()

                if isinstance(produced, str):
                    produced = produced.encode("utf-8")

                await self.set(key, produced, ttl=ttl, tags=tags)
                return produced

        except LockError:
            if inspect.iscoroutinefunction(producer):
                produced = await producer()
            else:
                produced = producer()

            if isinstance(produced, str):
                produced = produced.encode("utf-8")

            await self.set(key, produced, ttl=ttl, tags=tags)
            return produced
