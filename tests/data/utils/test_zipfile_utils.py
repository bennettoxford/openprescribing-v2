import zipfile

import pytest

from openprescribing.data.utils.zipfile_utils import extract_file_from_zip_archive


def test_extract_file_from_zip_archive(tmp_path):
    data = b"abcedf" * 1024
    zip_path = tmp_path / "file.zip"

    zf = zipfile.ZipFile(zip_path, "w")
    zf.writestr("data.txt", data)
    zf.close()

    dest_path = tmp_path / "extracted.txt"
    extract_file_from_zip_archive(zip_path, dest_path)
    assert dest_path.read_bytes() == data


def test_extract_file_from_zip_archive_non_unqiue_error(tmp_path):
    zip_path = tmp_path / "file.zip"

    zf = zipfile.ZipFile(zip_path, "w")
    zf.writestr("data.txt", b"")
    zf.writestr("data.other", b"")
    zf.close()

    with pytest.raises(AssertionError, match="Expected exactly one"):
        extract_file_from_zip_archive(zip_path, tmp_path / "extracted.txt")


def test_extract_file_from_zip_archive_with_condition(tmp_path):
    data = b"abcedf" * 1024
    zip_path = tmp_path / "file.zip"

    zf = zipfile.ZipFile(zip_path, "w")
    zf.writestr("data.txt", data)
    zf.writestr("data.other", b"")
    zf.close()

    dest_path = tmp_path / "extracted.txt"
    extract_file_from_zip_archive(
        zip_path,
        dest_path,
        condition=lambda zi: zi.filename.endswith(".txt"),
    )
    assert dest_path.read_bytes() == data
