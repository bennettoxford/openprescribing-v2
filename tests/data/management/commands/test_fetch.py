import io
import logging
from unittest.mock import Mock

from django.conf import settings
from django.core.management import call_command

from openprescribing.data.management.commands import fetch


def test_fetch_named_fetcher(monkeypatch):
    mock_fetcher_1 = Mock()
    mock_fetcher_2 = Mock()
    monkeypatch.setattr(
        fetch.Command,
        "available_fetchers",
        {
            "mock_fetcher_1": mock_fetcher_1,
            "mock_fetcher_2": mock_fetcher_2,
        },
    )

    call_command("fetch", ["mock_fetcher_1"])

    mock_fetcher_1.assert_called_once_with(settings.DOWNLOAD_DIR)
    mock_fetcher_2.assert_not_called()


def test_fetch_all(monkeypatch):
    mock_fetcher_1 = Mock()
    mock_fetcher_2 = Mock()
    monkeypatch.setattr(
        fetch.Command,
        "available_fetchers",
        {
            "mock_fetcher_1": mock_fetcher_1,
            "mock_fetcher_2": mock_fetcher_2,
        },
    )

    call_command("fetch", ["all"])

    mock_fetcher_1.assert_called_once()
    mock_fetcher_2.assert_called_once()


def test_fetch_logging(monkeypatch, freezer):
    log = logging.getLogger("openprescribing.data.fetchers")

    def fetcher(*_, **__):
        log.info("hello")
        log.info("world")

    def fetcher_2(*_, **__):
        log.info("another")

    monkeypatch.setattr(
        fetch.Command,
        "available_fetchers",
        {
            "fetcher": fetcher,
            "fetcher_2": fetcher_2,
        },
    )

    freezer.move_to("2025-01-02T03:04:05")
    stdout = io.StringIO()
    call_command("fetch", ["all"], stdout=stdout)
    assert stdout.getvalue() == (
        "2025-01-02T03:04:05 [  fetcher] hello\n"
        "2025-01-02T03:04:05 [  fetcher] world\n"
        "2025-01-02T03:04:05 [fetcher_2] another\n"
    )
