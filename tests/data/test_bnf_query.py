import pytest

from openprescribing.data.bnf_query import (
    BNFQuery,
    ProductType,
    _get_form_route_ids_for_forms_and_routes,
)
from openprescribing.data.models import BNFCode
from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


def test_init_normalizes_lists_to_tuples():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids=["1", "6"],
        ingredient_ids=["2"],
    )
    assert query == BNFQuery(
        bnf_codes=("01",),
        bnf_codes_excluded=("0101",),
        product_type=ProductType.GENERIC,
        form_route_ids=("1", "6"),
        ingredient_ids=("2",),
    )


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes(bnf_codes):
    query = BNFQuery(
        bnf_codes=["1001030U0AA", "1001030U0BD"], bnf_codes_excluded=["1001030U0AAABAB"]
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_no_excludes(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0AA"])
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_strength_and_formulation(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0_AC"])
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_generic(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_generic_with_strength_and_formulation(
    bnf_codes,
):
    query = BNFQuery(bnf_codes=["1001030U0_AB"], product_type=ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_branded(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_branded_with_strength_and_formulation(
    bnf_codes,
):
    query = BNFQuery(bnf_codes=["1001030U0_AB"], product_type=ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
    ]


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_matching_presentation_codes_for_form_route_ids(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    # The following appears in the dm+d -> BNF data/mapping data
    BNFCode(code="0203020C0AAAAAA", level=BNFCode.Level.PRESENTATION).save()
    # The following doesn't appear in the dm+d -> BNF data/mapping data
    BNFCode(code="1001030U0BDABAC", level=BNFCode.Level.PRESENTATION).save()
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "0203020C0AAAAAA",
            "ntr_form_route_ids": "0024",
        },
    )
    assert query.get_matching_presentation_codes() == ["0203020C0AAAAAA"]


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_matching_presentation_codes_for_ingredient_ids(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    # The following appears in the dm+d -> BNF data/mapping data
    BNFCode(code="1305020C0AAFVFV", level=BNFCode.Level.PRESENTATION).save()
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_ingredient_ids": "53034005",
        },
    )
    assert query.get_matching_presentation_codes() == ["1305020C0AAFVFV"]


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_matching_presentation_codes_for_ingredient_ids_no_match(
    rxdb, settings, tmp_path
):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    # The following appears in the dm+d -> BNF data/mapping data
    BNFCode(code="1305020C0AAFVFV", level=BNFCode.Level.PRESENTATION).save()
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_ingredient_ids": "999",
        },
    )
    assert query.get_matching_presentation_codes() == []


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_all_product_types(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0"], bnf_codes_excluded=["1001030U0_AB"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "includes": [
            {
                "code": "1001030U0",
                "description": "Methotrexate",
            }
        ],
        "excludes": [
            {
                "code": "1001030U0_AB",
                "description": "Methotrexate 2.5mg tablets (branded and generic)",
            }
        ],
        "form_routes": [],
        "ingredient_ids": [],
    }


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_generic_products(bnf_codes):
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        bnf_codes_excluded=["1001030U0_AB"],
        product_type=ProductType.GENERIC,
    )
    assert query.describe() == {
        "product_type": ProductType.GENERIC,
        "includes": [
            {
                "code": "1001030U0",
                "description": "Methotrexate",
            }
        ],
        "excludes": [
            {
                "code": "1001030U0_AB",
                "description": "Methotrexate 2.5mg tablets",
            }
        ],
        "form_routes": [],
        "ingredient_ids": [],
    }


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_describe_search_for_ingredients(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    query = BNFQuery(bnf_codes=[], ingredient_ids=["53034005"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "includes": [],
        "excludes": [],
        "form_routes": [],
        "ingredient_ids": [
            {
                "code": "53034005",
                "description": "Coal tar",
            }
        ],
    }


def test_from_params():
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
            "ntr_product_type": "generic",
        },
    )
    assert query == BNFQuery(
        bnf_codes=["01"], bnf_codes_excluded=["0101"], product_type=ProductType.GENERIC
    )


def test_has_params():
    assert BNFQuery.has_params("ntr", {"ntr_bnf_codes": "01"})
    assert BNFQuery.has_params("ntr", {"ntr_product_type": "generic"})
    assert BNFQuery.has_params("ntr", {"ntr_ingredient_ids": "01"})
    assert not BNFQuery.has_params("ntr", {"org_id": "PRAC01"})


def test_from_params_with_form_route_ids_key_not_val():
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "01",
            "ntr_product_type": "generic",
            "ntr_form_route_ids": "",
        },
    )
    assert query.form_route_ids == ()


def test_from_params_ingredients():
    query = BNFQuery.from_params("ntr", {"ntr_ingredient_ids": "01"})
    assert query == BNFQuery(
        bnf_codes=[], product_type=BNFQuery.PRODUCT_TYPE_DEFAULT, ingredient_ids=["01"]
    )


def test_to_params():
    query = BNFQuery(
        bnf_codes=["01"], bnf_codes_excluded=["0101"], product_type=ProductType.GENERIC
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
    }


def test_to_params_excluded_only():
    query = BNFQuery(bnf_codes_excluded=["0101"])
    assert query.to_params("ntr") == {
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "all",
    }


def test_to_params_with_form_route_ids():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids=("1", "6"),
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
        "ntr_form_route_ids": "1,6",
    }


def test_to_params_with_ingredient_ids():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        ingredient_ids=("1"),
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
        "ntr_ingredient_ids": "1",
    }


@pytest.mark.django_db(databases=["data"])
def test_from_dict():
    test_dict = {
        "bnf_codes": {
            "included": ["01"],
        }
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_generic():
    test_dict = {
        "bnf_codes": {
            "included": ["01"],
            "excluded": ["0101"],
        },
        "product_type": "generic",
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_from_dict_form_route(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    # The following appears in the dm+d -> BNF data/mapping data
    BNFCode(code="0203020C0AAAAAA", level=BNFCode.Level.PRESENTATION).save()

    test_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "form_routes": ["solutioninjection.intravenous"],
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_from_dict_separate_form_route(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    test_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "forms": ["solutioninjection"],
        "routes": ["intravenous"],
    }
    query = BNFQuery.from_dict(test_dict)
    expected_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "form_routes": ["solutioninjection.intravenous"],
    }
    assert query.to_dict() == expected_dict


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_form_route_ids_for_forms_and_routes(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    route_ids = _get_form_route_ids_for_forms_and_routes(
        form_routes=[], forms=["tablet"], routes=["oral"]
    )
    expected_route_ids = ["1"]

    assert route_ids == expected_route_ids


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_form_route_ids_for_invalid_form_routes(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    with pytest.raises(ValueError):
        _get_form_route_ids_for_forms_and_routes(
            form_routes=[], forms=["unicorn"], routes=[]
        )

    with pytest.raises(ValueError):
        _get_form_route_ids_for_forms_and_routes(
            form_routes=["unicorn.nasal"], forms=[], routes=[]
        )

    with pytest.raises(ValueError):
        _get_form_route_ids_for_forms_and_routes(
            form_routes=[], forms=[], routes=["interstellar"]
        )


@pytest.mark.django_db(databases=["data"])
def test_from_dict_ingredient():
    test_dict = {
        "ingredient_ids": ["53034005"],
    }

    query = BNFQuery.from_dict(test_dict)
    computed_dict = query.to_dict()

    assert computed_dict["ingredient_ids"] == ["53034005"]
