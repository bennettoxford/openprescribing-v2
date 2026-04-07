import shutil
from pathlib import Path

from openprescribing.data.fetchers.dmd.fetcher import extract_data_from_directory
from openprescribing.data.ingestors import dmd


def ingest_dmd_data(settings, tmp_path):
    """Ingest dmd data.

    settings and tmp_path are pytest fixtures.
    """

    prepare_for_dmd_ingest(settings, tmp_path)
    dmd.ingest()


def prepare_for_dmd_ingest(settings, tmp_path):
    """Set up DOWNLOAD_DIR to be in the state it would be in after dmd fetcher has run."""

    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    tmp_dir = tmp_path / "tmp"
    shutil.copytree(Path("tests/fixtures/dmd"), tmp_dir / "xml")
    (tmp_dir / "csv").mkdir()
    release_dir = settings.DOWNLOAD_DIR / "dmd" / "dmd_2026-03-30_3.4.0_20260330000001"
    release_dir.mkdir(parents=True)
    extract_data_from_directory(tmp_dir, release_dir)
