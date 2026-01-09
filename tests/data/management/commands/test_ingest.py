import io
import logging
from unittest.mock import Mock

import django.db
import pytest
from django.core.management import call_command

import openprescribing.data.ingestors
from openprescribing.data.management.commands import ingest


pytestmark = pytest.mark.django_db(databases=["data"])


def test_available_ingestors():
    assert openprescribing.data.ingestors.available_ingestors == {
        "bnf_codes": openprescribing.data.ingestors.bnf_codes.ingest,
        "ods": openprescribing.data.ingestors.ods.ingest,
        "prescribing": openprescribing.data.ingestors.prescribing.ingest,
    }


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

    mock_ingestor_1.assert_called_once_with(force=False)
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

    mock_ingestor_1.assert_called_once_with(force=False)
    mock_ingestor_2.assert_called_once_with(force=False)


def test_ingest_force(monkeypatch):
    mock_ingestor_1 = Mock()
    monkeypatch.setattr(
        ingest.Command,
        "available_ingestors",
        {"mock_ingestor_1": mock_ingestor_1},
    )

    call_command("ingest", ["mock_ingestor_1", "--force"])

    mock_ingestor_1.assert_called_once_with(force=True)


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


def test_ingest_logging_quiet(monkeypatch, freezer):
    log = logging.getLogger("openprescribing.data.ingestors")

    def ingestor(*_, **__):
        log.debug("this should not appear")
        log.info("but this should")

    monkeypatch.setattr(
        ingest.Command,
        "available_ingestors",
        {"ingestor": ingestor},
    )

    freezer.move_to("2025-01-02T03:04:05")
    stdout = io.StringIO()
    call_command("ingest", ["ingestor", "--quiet"], stdout=stdout)
    assert stdout.getvalue() == "2025-01-02T03:04:05 [ingestor] but this should\n"


def test_ingest_ensures_main_database_file_is_updated(tmp_path, monkeypatch, settings):
    # Create a test database which exists as a file on disk (the default test database
    # is in-memory which is no good for our purposes here)
    sqlite_path = tmp_path / "data.sqlite"
    settings.DATABASES["data"]["NAME"] = sqlite_path
    monkeypatch.delattr(django.db.connections._connections, "data")

    with django.db.connections["data"].cursor() as cursor:
        cursor.execute("CREATE TABLE t (v INT)")

    initial_mtime = sqlite_path.stat().st_mtime

    def ingestor(*_, **__):
        with django.db.connections["data"].cursor() as cursor:
            cursor.execute("INSERT INTO t VALUES (1), (2)")

    # Run the ingestor directly and confirm that while it has inserted data the file
    # modification timestamp has not changed
    ingestor()
    with django.db.connections["data"].cursor() as cursor:
        assert cursor.execute("SELECT v FROM t").fetchall() == [(1,), (2,)]
    assert sqlite_path.stat().st_mtime == initial_mtime

    # Run the ingestor via the management command and confirm that it has now updated
    # the timestamp
    monkeypatch.setattr(ingest.Command, "available_ingestors", {"ingestor": ingestor})
    call_command("ingest", ["ingestor"])
    with django.db.connections["data"].cursor() as cursor:
        assert cursor.execute("SELECT v FROM t").fetchall() == [(1,), (2,), (1,), (2,)]
    assert sqlite_path.stat().st_mtime > initial_mtime
