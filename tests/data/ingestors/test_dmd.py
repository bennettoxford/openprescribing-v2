import shutil

import pytest

from openprescribing.data.ingestors import dmd
from openprescribing.data.models.dmd import AMPP, VMP
from tests.utils.ingest_utils import prepare_for_dmd_ingest


@pytest.mark.django_db(databases=["data"])
def test_dmd_ingest(settings, tmp_path):
    prepare_for_dmd_ingest(settings, tmp_path)

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

    # This is a regression test to ensure that we handle object deletion correctly.  We
    # delete all objects before (re)creating new ones.  Previously we did this
    # incorrectly, and cascading model deletion led to the deletion of objects that had
    # only just been created.
    dmd.ingest(force=True)
    assert VMP.objects.filter(pk=28946311000001106).exists()

    # Attempting to re-ingest the same named file without forcing should do nothing. As
    # a simple check for this we delete tmp_dir and re-ingest. If the code does attempt
    # to load it then this will fail loudly.
    shutil.rmtree(tmp_path / "tmp")
    dmd.ingest()
