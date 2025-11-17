import pytest

import openprescribing.data.rxdb
from tests.utils.rxdb_utils import RXDBFixture


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if terminalreporter.stats.get("warnings"):  # pragma: no cover
        print(
            "\nFailing test suite due to presence of warnings.\n"
            "Uninteresting warnings should be explicitly ignored (usually in pyproject.toml)"
        )
        if terminalreporter._session.exitstatus == 0:
            terminalreporter._session.exitstatus = 13


@pytest.fixture
def rxdb(monkeypatch):
    rxdb_fixture = RXDBFixture()
    monkeypatch.setattr(
        openprescribing.data.rxdb, "get_cursor", rxdb_fixture.get_cursor
    )
    yield rxdb_fixture


@pytest.fixture(scope="session", autouse=True)
def prevent_rxdb_access():
    def get_cursor():  # pragma: no cover
        raise RuntimeError(
            "Direct access to the rxdb database is not allowed in tests; "
            "use the `rxdb` fixture to enable it"
        )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(openprescribing.data.rxdb, "get_cursor", get_cursor)
        yield
