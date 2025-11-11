import pytest
import requests
import responses

from openprescribing.data.utils.http_session import HTTPSession


@responses.activate
def test_url_base():
    responses.get(
        "http://example.com/api/test/path",
        body="hello",
    )

    http = HTTPSession("http://example.com/api/")
    rsp = http.get("test/path")
    assert rsp.text == "hello"


@responses.activate
def test_raise_for_response():
    responses.get(
        "http://example.com/",
        status=404,
    )

    http = HTTPSession("")
    with pytest.raises(requests.HTTPError):
        http.get("http://example.com/")


@responses.activate
def test_log():
    responses.get(
        "http://example.com/",
    )

    logs = []
    http = HTTPSession("", log=logs.append)
    http.get("http://example.com/", params={"foo": "bar"})

    assert logs == ["GET http://example.com/?foo=bar"]


@responses.activate
def test_download_to_file(tmp_path):
    dest_path = tmp_path / "dest"
    body = b"abcef" * 1024
    responses.get(
        "http://example.com/",
        body=body,
    )

    http = HTTPSession("")
    http.download_to_file("http://example.com/", dest_path, buffer_size=1024)

    assert dest_path.read_bytes() == body
