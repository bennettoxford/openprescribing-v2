import pytest

from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_medications(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)

    # Confirm that we can query the medications table.
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            "SELECT * FROM medications WHERE id = 4744411000001104"
        )
        assert results.fetchall() == [
            (
                4744411000001104,  # id
                "0203020C0BBAAAA",  # bnf_code
                "Adenocor 6mg/2ml solution for injection vials (Sanofi)",  # name
                True,  # is_amp
                35894711000001106,  # vmp_id
                108502004,  # vtm_id
                False,  # invalid
                [24],  # form_route_ids
                [35431001],  # ingredient_ids
            )
        ]
