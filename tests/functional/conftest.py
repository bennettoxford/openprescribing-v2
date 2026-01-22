import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_env():
    # This is required for playwright tests with Django
    # See https://github.com/microsoft/playwright-pytest/issues/29
    # As well as these:
    # https://github.com/opensafely-core/airlock/blob/a98c2985af68ada7ae31aac3aca384590328b709/tests/functional/conftest.py#L51
    # https://github.com/opensafely-core/opencodelists/issues/2408
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"
