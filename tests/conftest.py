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
