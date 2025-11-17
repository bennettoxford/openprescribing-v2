import pytest

import openprescribing.data.rxdb
from tests.utils.rxdb_utils import RXDBFixture


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
