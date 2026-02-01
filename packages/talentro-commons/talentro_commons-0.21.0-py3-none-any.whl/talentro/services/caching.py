import os
from functools import wraps
from typing import Any, List

from aiocache import RedisCache
from aiocache.serializers import PickleSerializer

from ..util.singleton import SingletonMeta


class CacheService(metaclass=SingletonMeta):

    def __init__(self):
        endpoint = os.environ.get('CACHE_ENDPOINT', 'localhost')
        port = os.environ.get('CACHE_PORT', 6379)

        self._cache = RedisCache(endpoint=endpoint, port=port, serializer=PickleSerializer())

    @staticmethod
    def _get_namespace_and_key(key: str) -> tuple[str, str]:
        key_parts = key.split(":")
        return ':'.join(key_parts[1:]), key_parts[0]

    async def get(self, key: str) -> Any:
        key, namespace = self._get_namespace_and_key(key)

        if value := await self._cache.get(key, namespace=namespace):
            return value

        return None

    async def set(self, key, value, ttl=300):
        key, namespace = self._get_namespace_and_key(key)
        return await self._cache.set(key, value, ttl=ttl, namespace=namespace)

    async def delete(self, key):
        key, namespace = self._get_namespace_and_key(key)
        await self._cache.delete(key, namespace=namespace)


def cache_response(namespace: str, include_keys: List[str] = list, ttl: int = 300, debug=False):
    """
    Caching decorator for FastAPI endpoints.

    ttl: Time to live for the cache in seconds.
    namespace: Namespace for cache keys in Redis.
    """
    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                cache: CacheService = CacheService()
            except Exception as e:
                print(f"Error creating cache: {e}")
                return await func(*args, **kwargs)

            cache_key = f"{namespace}"

            # If organization is specific, add organization id to the cache key
            if organization_id := kwargs.get("x_organization_id"):
                cache_key += f":org:{organization_id}"

            for key in include_keys:
                value = kwargs.get(key)
                if value is not None:
                    cache_key += f":{key}:{value}"

            if debug:
                print(f"Cache key {cache_key}")

            # Try to retrieve data from cache
            try:
                if cached_value := await cache.get(cache_key):
                    return cached_value  # Return cached data
            except Exception as e:
                print(f"Error retrieving data from cache: {e}")

            response = await func(*args, **kwargs)

            try:
                if response is not None:
                    # Store the response in Redis with a TTL
                    await cache.set(cache_key, response, ttl=ttl)
            except Exception as e:
                print(f"Error caching data: {e}")

            return response

        return wrapper

    return decorator
