import importlib
import os
import sys

from openprescribing.data.utils.load_package_modules import (
    load_all_modules_with_function,
)


def create_test_package_files(tmp_path, package_name):
    package_path = tmp_path / package_name
    os.mkdir(package_path)
    with open(package_path / "__init.py__", "w") as f:
        f.write("")

    test_modules = ["test_fetch1", "test_fetch2"]
    test_content = """
def fetch():
    return "data"
    """

    for test_module in test_modules:
        with open(package_path / f"{test_module}.py", "w") as f:
            f.write(test_content)

    return package_path


def test_load_all_modules_with_function(tmp_path):
    package_name = "mypackage"
    package_path = create_test_package_files(tmp_path, package_name)

    try:
        sys.path.insert(0, str(tmp_path))
        functions = load_all_modules_with_function(
            [str(package_path)], package_name, "fetch"
        )
        mypackage = importlib.import_module(package_name)
        assert functions == {
            "test_fetch1": mypackage.test_fetch1.fetch,
            "test_fetch2": mypackage.test_fetch2.fetch,
        }

    finally:
        sys.path.remove(str(tmp_path))
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(package_name):
                del sys.modules[module_name]
