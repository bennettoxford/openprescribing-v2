import shutil
from pathlib import Path

import pytest

from openprescribing.data.fetchers.dmd.fetcher import extract_data_from_directory
from openprescribing.data.ingestors import dmd
from openprescribing.data.models.dmd import AMPP, VMP


@pytest.mark.django_db(databases=["data"])
def test_bnf_codes_ingest(settings, tmp_path):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    release_dir = settings.DOWNLOAD_DIR / "dmd" / "dmd_2026-03-30_3.4.0_20260330000001"
    release_dir.mkdir(parents=True)
    tmp_dir = tmp_path / "tmp"

    # Set up tmp_dir so that it's in the state it would be in after the fetcher has
    # fetched and unzipped the dm+d data files, but before it has converted the XML to
    # parquet.
    shutil.copytree(Path("tests/fixtures/dmd"), tmp_dir / "xml")
    (tmp_dir / "csv").mkdir()

    # Extract data from XML files to parquet.
    extract_data_from_directory(tmp_dir, release_dir)

    dmd.ingest()

    # Make some spot-check assertions about the ORM objects that have been created by
    # the ingest process.  This includes checking the special cases as described in
    # ingestors.dmd.build_instance.
    vmp = VMP.objects.get(pk=28946311000001106)
    assert vmp.nm == "Coal tar 10% / Salicylic acid 5% in Aqueous cream"
    assert vmp.invalid is False
    assert vmp.pres_stat.descr == "Valid as a prescribable product"

    ampp = AMPP.objects.get(pk=28781811000001106)
    assert (
        ampp.nm
        == "Coal tar solution 10% / Salicylic acid 5% in Aqueous cream (Special Order) 1 gram"
    )
    assert ampp.reimbinfo.dnd.descr == "Discount not deducted - automatic"

    # Attempting to re-ingest the same named file should do nothing. As a simple check for
    # this we delete tmp_dir and re-ingest. If the code does attempt to load it then this
    # will fail loudly.
    shutil.rmtree(tmp_dir)
    dmd.ingest()
