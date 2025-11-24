import io
import sqlite3
import subprocess

import duckdb
from django.core.management import call_command

from openprescribing.data.management.commands import rxdbshell


def test_rxdbshell(tmp_path, settings, monkeypatch):
    settings.PRESCRIBING_DATABASE = tmp_path / "prescribing.duckdb"
    settings.SQLITE_DATABASE = tmp_path / "data.sqlite"

    # Write some values into the SQLite database
    sqlite_conn = sqlite3.connect(settings.SQLITE_DATABASE)
    sqlite_conn.executescript(
        """
        CREATE TABLE foo (v INT);
        INSERT INTO foo VALUES (1), (2), (3);
        """
    )
    sqlite_conn.close()

    # Write some values into the DuckDB database
    duckdb_conn = duckdb.connect(settings.PRESCRIBING_DATABASE)
    duckdb_conn.sql(
        """
        CREATE TABLE bar (v INT);
        INSERT INTO bar VALUES (4), (5), (6);
        """
    )
    duckdb_conn.close()

    fake_exec = FakeExec(
        # Select results from both databases (showing both are mounted) and get results
        # as CSV
        input=".mode csv\nSELECT * FROM foo UNION ALL SELECT * FROM bar",
        check=True,
        text=True,
        capture_output=True,
    )
    monkeypatch.setattr(rxdbshell.os, "execvp", fake_exec.execvp)

    call_command("rxdbshell", stderr=io.StringIO())

    assert fake_exec.stdout == "v\n1\n2\n3\n4\n5\n6\n"


# The `os.exec*` family of commands replace the currently running process so they can't
# be tested directly. Instead we replace them with a suitable configured
# `subprocess.run()` so we can get access to the output.
class FakeExec:
    def __init__(self, **run_kwargs):
        self.run_kwargs = run_kwargs
        self.proc = None

    def execvp(self, executable, args):
        self.proc = subprocess.run(
            args,
            executable=executable,
            **self.run_kwargs,
        )

    @property
    def stdout(self):
        assert self.proc is not None, "Process has not been run"
        return self.proc.stdout
