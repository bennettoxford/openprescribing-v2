import pytest

from openprescribing.config import settings as settings_module


def test_get_env_var():
    with pytest.raises(
        RuntimeError, match="Missing environment variable: AINT_NO_SUCH_VAR"
    ):
        settings_module.get_env_var("AINT_NO_SUCH_VAR")
