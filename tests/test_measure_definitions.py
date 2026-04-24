import pytest

from openprescribing.data.measures import all_measure_details, load_measure
from tests.utils.ingest_utils import ingest_dmd_data


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_load_all_measures(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    for measure in all_measure_details():
        load_measure(measure["name"])
