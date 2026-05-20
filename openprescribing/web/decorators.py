from django.conf import settings
from django.views.decorators.cache import cache_control
from django.views.decorators.http import etag

from openprescribing.data import rxdb


def add_cache_headers(view_fn):
    """Add headers telling clients to cache response and revalidate on every request."""

    cache_control_kwargs = {"public": True, "max_age": 0, "must_revalidate": True}

    def get_etag(request):
        duckdb_mtime, sqlite_mtime = rxdb.get_cache_key()
        return f"{settings.VERSION}-{duckdb_mtime}-{sqlite_mtime}"

    return cache_control(**cache_control_kwargs)(etag(get_etag)(view_fn))
