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
