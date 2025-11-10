import io
import logging
from unittest.mock import Mock

from django.core.management import call_command

from openprescribing.data.management.commands import ingest


def test_ingest_named_ingestor(monkeypatch):
    mock_ingestor_1 = Mock()
    mock_ingestor_2 = Mock()
    monkeypatch.setattr(
        ingest.Command,
        "available_ingestors",
        {
            "mock_ingestor_1": mock_ingestor_1,
            "mock_ingestor_2": mock_ingestor_2,
        },
    )

    call_command("ingest", ["mock_ingestor_1"])

    mock_ingestor_1.assert_called_once()
    mock_ingestor_2.assert_not_called()


def test_ingest_all(monkeypatch):
    mock_ingestor_1 = Mock()
    mock_ingestor_2 = Mock()
    monkeypatch.setattr(
        ingest.Command,
        "available_ingestors",
        {
            "mock_ingestor_1": mock_ingestor_1,
            "mock_ingestor_2": mock_ingestor_2,
        },
    )

    call_command("ingest", ["all"])

    mock_ingestor_1.assert_called_once()
    mock_ingestor_2.assert_called_once()


def test_ingest_logging(monkeypatch, freezer):
    log = logging.getLogger("openprescribing.data.ingestors")

    def ingestor(*_, **__):
        log.info("hello")
        log.info("world")

    def ingestor_2(*_, **__):
        log.info("another")

    monkeypatch.setattr(
        ingest.Command,
        "available_ingestors",
        {
            "ingestor": ingestor,
            "ingestor_2": ingestor_2,
        },
    )

    freezer.move_to("2025-01-02T03:04:05")
    stdout = io.StringIO()
    call_command("ingest", ["all"], stdout=stdout)
    assert stdout.getvalue() == (
        "2025-01-02T03:04:05 [  ingestor] hello\n"
        "2025-01-02T03:04:05 [  ingestor] world\n"
        "2025-01-02T03:04:05 [ingestor_2] another\n"
    )
