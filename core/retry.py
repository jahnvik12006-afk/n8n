import asyncio
import random
from functools import wraps

from core.config import config
from core.logger import logger


def with_retry(max_attempts: int | None = None):
    max_attempts = max_attempts or config.MAX_RETRY

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts:
                        delay = min(2 ** attempt * 2, 30) + random.uniform(0, 2)
                        logger.warning(
                            "%s attempt %d/%d failed: %s. Retrying in %.1fs...",
                            func.__name__, attempt, max_attempts, e, delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, e,
                        )
            raise last_exc
        return wrapper
    return decorator
