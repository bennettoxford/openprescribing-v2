import pytest

from openprescribing.data.ingestors import dmd_bnf_map
from openprescribing.data.models import DmdBnfMap
from tests.utils.ingest_utils import prepare_for_dmd_bnf_map_ingest


@pytest.mark.django_db(databases=["data"])
def test_dmd_bnf_map_ingest(settings, tmp_path):
    prepare_for_dmd_bnf_map_ingest(settings, tmp_path)
    dmd_bnf_map.ingest()

    # This dm+d objects has a BNF code in the mapping...
    assert DmdBnfMap.objects.get(dmd_id=19663311000001109).bnf_code == "0203020C0AAAAAA"

    # ...but this one does not.
    assert not DmdBnfMap.objects.filter(dmd_id=10837011000001103).exists()

    # Attempting to re-ingest the same named file should do nothing. As a simple check for
    # this we empty the file contents and re-ingest. If the code does attempt to load it
    # then this will fail loudly.
    (settings.DOWNLOAD_DIR / "dmd_bnf_map" / "map.parquet").write_text("")
    dmd_bnf_map.ingest()
