import functools

from django.conf import settings
from django.views.decorators.cache import cache_control
from django.views.decorators.http import etag

from openprescribing.data import rxdb


def cache(fn):
    """Cache a no-argument function's return value in memory until the underlying data
    changes.

    Unlike add_cache_headers, we don't include settings.VERSION in the cache key,
    because if this changes, the server will be restarted and the in-memory cache will
    be cleared.
    """

    @functools.lru_cache(maxsize=1)
    def cached(cache_key):
        return fn()

    @functools.wraps(fn)
    def wrapper():
        return cached(rxdb.get_cache_key())

    return wrapper


def add_cache_headers(view_fn):
    """Add headers telling clients to cache response and revalidate on every request."""

    cache_control_kwargs = {"public": True, "max_age": 0, "must_revalidate": True}

    def get_etag(request):
        duckdb_mtime, sqlite_mtime = rxdb.get_cache_key()
        return f"{settings.VERSION}-{duckdb_mtime}-{sqlite_mtime}"

    return cache_control(**cache_control_kwargs)(etag(get_etag)(view_fn))
