import math
import time

from redis.asyncio import Redis

PREFIX = "careready:revoked:"


async def add_jti_to_blocklist(redis: Redis, jti: str, expires_at: int) -> None:
    # Never keep a revocation forever, or expire it before the JWT itself.
    ttl = math.ceil(expires_at - time.time())
    if ttl > 0:
        await redis.set(PREFIX + jti, "1", ex=ttl)


async def token_in_blocklist(redis: Redis, jti: str) -> bool:
    return bool(await redis.exists(PREFIX + jti))
