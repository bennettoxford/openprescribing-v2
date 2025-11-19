import tempfile
from pathlib import Path

from openprescribing.data.utils.csv_to_parquet import csv_to_parquet
from openprescribing.data.utils.filename_utils import get_temp_filename_for
from openprescribing.data.utils.zipfile_utils import extract_file_from_zip_archive


def remote_csv_to_parquet(http, csv_url, output_filename, **parquet_kwargs):
    with tempfile.TemporaryDirectory() as tmp_name:
        csv_path = Path(tmp_name) / "file.csv"
        http.download_to_file(csv_url, csv_path)
        csv_to_parquet_atomic(csv_path, output_filename, **parquet_kwargs)


def remote_zipped_csv_to_parquet(http, zip_url, output_filename, **parquet_kwargs):
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp_dir = Path(tmp_name)
        zip_path = tmp_dir / "file.zip"
        csv_path = tmp_dir / "file.csv"

        http.download_to_file(zip_url, zip_path)
        extract_file_from_zip_archive(
            zip_path,
            csv_path,
            condition=lambda zipinfo: zipinfo.filename.lower().endswith(".csv"),
        )
        csv_to_parquet_atomic(csv_path, output_filename, **parquet_kwargs)


def csv_to_parquet_atomic(csv_path, parquet_path, **parquet_kwargs):
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_tmp = get_temp_filename_for(parquet_path)
    csv_to_parquet(csv_path, parquet_tmp, **parquet_kwargs)
    parquet_tmp.replace(parquet_path)
