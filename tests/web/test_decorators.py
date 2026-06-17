import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from openprescribing.web.decorators import add_cache_headers, cache


@add_cache_headers
def view(request):
    return HttpResponse("hello")


@pytest.fixture
def patch_cache_key(monkeypatch):
    def patch(version, duckdb_mtime, sqlite_mtime):
        monkeypatch.setattr("openprescribing.web.decorators.settings.VERSION", version)
        monkeypatch.setattr(
            "openprescribing.web.decorators.rxdb.get_cache_key",
            lambda: (duckdb_mtime, sqlite_mtime),
        )

    return patch


def test_cache(patch_cache_key):
    calls = 0

    @cache
    def fn():
        nonlocal calls
        calls += 1

    patch_cache_key("aaaaaaa", 100.0, 200.0)
    fn()
    assert calls == 1
    fn()
    assert calls == 1

    patch_cache_key("aaaaaaa", 300.0, 400.0)
    fn()
    assert calls == 2
    fn()
    assert calls == 2


def test_etag_and_cache_control_headers_on_200(patch_cache_key):
    patch_cache_key("aaaaaaa", 100.0, 200.0)

    rsp = view(RequestFactory().get("/"))

    assert rsp.status_code == 200
    assert rsp["ETag"] == '"aaaaaaa-100.0-200.0"'
    assert rsp["Cache-Control"] == "public, max-age=0, must-revalidate"


def test_cache_hit_returns_304(patch_cache_key):
    patch_cache_key("aaaaaaa", 100.0, 200.0)

    rsp = view(RequestFactory().get("/", HTTP_IF_NONE_MATCH='"aaaaaaa-100.0-200.0"'))

    assert rsp.status_code == 304
    assert rsp["ETag"] == '"aaaaaaa-100.0-200.0"'
    assert rsp["Cache-Control"] == "public, max-age=0, must-revalidate"


def test_cache_miss_returns_200(patch_cache_key):
    patch_cache_key("bbbbbbb", 100.0, 200.0)

    rsp = view(RequestFactory().get("/", HTTP_IF_NONE_MATCH='"aaaaaaa-100.0-200.0"'))

    assert rsp.status_code == 200
    assert rsp["ETag"] == '"bbbbbbb-100.0-200.0"'
    assert rsp["Cache-Control"] == "public, max-age=0, must-revalidate"
