import pytest

from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_medications(rxdb, settings, tmp_path):
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)

    # Confirm that we can query the medications table.
    with rxdb.get_cursor() as cursor:
        # A VMP with multiple ingredients
        results = cursor.execute(
            "SELECT * FROM medications WHERE id = 28946311000001106"
        )
        assert results.fetchall() == [
            (
                28946311000001106,  # id
                "1305020C0AAFVFV",  # bnf_code
                "Coal tar 10% / Salicylic acid 5% in Aqueous cream",  # name
                False,  # is_amp
                28946311000001106,  # vmp_id
                15219611000001105,  # vtm_id
                False,  # invalid
                [],  # form_route_ids
                [387253001, 53034005],  # ingredient_ids
            )
        ]

        # An AMP with its own BNF code
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

        # An AMP with no BNF code
        results = cursor.execute(
            "SELECT * FROM medications WHERE id = 10837011000001103"
        )
        assert results.fetchall() == [
            (
                10837011000001103,  # id
                None,  # bnf_code
                "Nutrison liquid (Waymade Healthcare Plc)",  # name
                True,  # is_amp
                3549611000001100,  # vmp_id
                None,  # vtm_id
                False,  # invalid
                [26],  # form_route_ids
                [],  # ingredient_ids
            )
        ]
