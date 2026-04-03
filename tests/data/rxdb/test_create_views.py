import pytest

from openprescribing.data.rxdb import connection
from tests.utils.dmd_utils import ingest_dmd_data


@pytest.mark.django_db(databases=["data"])
def test_medications(settings, tmp_path):
    ingest_dmd_data(settings, tmp_path)

    # Confirm that we can query the medications table.
    with connection.get_cursor() as cursor:
        results = cursor.execute(
            "SELECT * FROM medications WHERE id = 4744411000001104"
        )
        assert results.fetchall() == [
            (
                4744411000001104,  # id
                "Adenocor 6mg/2ml solution for injection vials (Sanofi)",  # name
                True,  # is_amp
                35894711000001106,  # vmp_id
                774441009,  # vtm_id
                False,  # invalid
                [24],  # form_route_ids
                [35431001],  # ingredient_ids
            )
        ]
