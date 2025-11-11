from datetime import date
from pathlib import Path

from openprescribing.data.utils import filename_utils


def test_get_latest_files_by_date():
    files = [
        Path("dir/.hidden"),
        Path("dir/test_2025-01-01_0002.txt"),
        Path("dir/test_2025-01-01_0003.txt"),
        Path("dir/test_2025-01-01_0001.txt"),
        Path("dir/test_2020-01-01_whatever.txt"),
    ]
    assert filename_utils.get_latest_files_by_date(files) == {
        date(2020, 1, 1): Path("dir/test_2020-01-01_whatever.txt"),
        date(2025, 1, 1): Path("dir/test_2025-01-01_0003.txt"),
    }


def test_get_temp_filename_for():
    filename = Path("a/b/some_file_name.txt")
    temp_filename = filename_utils.get_temp_filename_for(filename)

    assert temp_filename.parent == filename.parent
    assert temp_filename.name.startswith(".")
    assert temp_filename.name.endswith(".tmp")
    assert len(temp_filename.name) > len(filename.name)
