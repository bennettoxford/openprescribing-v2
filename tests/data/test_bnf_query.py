import pytest

from openprescribing.data.bnf_query import (
    BNFQuery,
    ProductType,
    _get_form_route_ids_for_forms_and_routes,
)
from openprescribing.data.models import BNFCode


def test_init_normalizes_lists_to_tuples():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids=["1", "6"],
        form_route_ids_excluded=["7"],
        ingredient_ids=["2"],
        ingredient_ids_excluded=["3"],
        vtm_ids=["4"],
        vtm_ids_excluded=["5"],
    )
    assert query == BNFQuery(
        bnf_codes=("01",),
        bnf_codes_excluded=("0101",),
        product_type=ProductType.GENERIC,
        form_route_ids=("1", "6"),
        form_route_ids_excluded=("7",),
        ingredient_ids=("2",),
        ingredient_ids_excluded=("3",),
        vtm_ids=("4",),
        vtm_ids_excluded=("5",),
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
def test_get_matching_presentation_codes_for_form_route_ids(dmd_data):
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
def test_get_matching_presentation_codes_for_ingredient_ids(dmd_data):
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
def test_get_matching_presentation_codes_for_ingredient_ids_no_match(dmd_data):
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


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_matching_presentation_codes_for_vtm_ids(dmd_data):
    BNFCode(code="1305020C0AAFVFV", level=BNFCode.Level.PRESENTATION).save()
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_vtm_ids": "15219611000001105",
        },
    )
    assert query.get_matching_presentation_codes() == ["1305020C0AAFVFV"]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_vtm_ids_excluded(bnf_codes, monkeypatch):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_vtm_ids",
        lambda ids: {
            ("90356005",): ["1001030U0AAABAB", "1001030U0AAACAC"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        vtm_ids_excluded=["90356005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_form_route_ids_excluded(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_form_route_ids",
        lambda ids: {
            ("24",): ["1001030U0AAABAB", "1001030U0BDAAAB"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        form_route_ids_excluded=["24"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_form_route_ids_include_and_exclude(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_form_route_ids",
        lambda ids: {
            ("1",): [
                "1001030U0AAABAB",
                "1001030U0AAACAC",
                "1001030U0BDAAAB",
                "1001030U0BDABAC",
            ],
            ("24",): ["1001030U0AAABAB", "1001030U0BDAAAB"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        form_route_ids=["1"],
        form_route_ids_excluded=["24"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_form_route_ids_excluded_no_match(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_form_route_ids",
        lambda ids: [],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0AA"],
        form_route_ids_excluded=["999"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_ingredient_ids_excluded(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_ingredient_ids",
        lambda ids: {
            ("53034005",): ["1001030U0AAACAC", "1001030U0BDABAC"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0BDAAAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_ingredient_ids_include_and_exclude(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_ingredient_ids",
        lambda ids: {
            ("methotrexate",): [
                "1001030U0AAABAB",
                "1001030U0AAACAC",
                "1001030U0BDAAAB",
                "1001030U0BDABAC",
            ],
            ("53034005",): ["1001030U0AAACAC", "1001030U0BDABAC"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        ingredient_ids=["methotrexate"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0BDAAAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_ingredient_ids_excluded_no_match(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_ingredient_ids",
        lambda ids: [],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0AA"],
        ingredient_ids_excluded=["missing"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_with_combined_exclusions(
    bnf_codes, monkeypatch
):
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_form_route_ids",
        lambda ids: {
            ("tablet",): [
                "1001030U0AAABAB",
                "1001030U0AAACAC",
                "1001030U0BDAAAB",
                "1001030U0BDABAC",
            ],
            ("24",): ["1001030U0AAABAB", "1001030U0BDAAAB"],
        }[tuple(ids)],
    )
    monkeypatch.setattr(
        "openprescribing.data.bnf_query._get_bnf_codes_for_ingredient_ids",
        lambda ids: {
            ("methotrexate",): [
                "1001030U0AAABAB",
                "1001030U0AAACAC",
                "1001030U0BDAAAB",
                "1001030U0BDABAC",
            ],
            ("53034005",): ["1001030U0BDABAC"],
        }[tuple(ids)],
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        bnf_codes_excluded=["1001030U0AAABAB"],
        form_route_ids=["tablet"],
        form_route_ids_excluded=["24"],
        ingredient_ids=["methotrexate"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == ["1001030U0AAACAC"]


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_all_product_types(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0"], bnf_codes_excluded=["1001030U0_AB"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": ["Methotrexate"],
        "bnf_codes_excluded": ["Methotrexate 2.5mg tablets (branded and generic)"],
        "form_routes": [],
        "form_routes_excluded": [],
        "ingredients": [],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
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
        "bnf_codes": ["Methotrexate"],
        "bnf_codes_excluded": ["Methotrexate 2.5mg tablets"],
        "form_routes": [],
        "form_routes_excluded": [],
        "ingredients": [],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_describe_search_for_ingredients(dmd_data):
    query = BNFQuery(bnf_codes=[], ingredient_ids=["53034005"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": [],
        "bnf_codes_excluded": [],
        "form_routes": [],
        "form_routes_excluded": [],
        "ingredients": ["Coal tar"],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_describe_search_for_all_filter_types(dmd_data, bnf_codes):
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        bnf_codes_excluded=["1001030U0_AB"],
        form_route_ids=["6"],
        form_route_ids_excluded=["5"],
        ingredient_ids=["53034005"],
        ingredient_ids_excluded=["35431001"],
        vtm_ids=["15219611000001105"],
        vtm_ids_excluded=["108502004"],
    )
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": ["Methotrexate"],
        "bnf_codes_excluded": ["Methotrexate 2.5mg tablets (branded and generic)"],
        "form_routes": ["suspension.oral"],
        "form_routes_excluded": ["solution.oral"],
        "ingredients": ["Coal tar"],
        "ingredients_excluded": ["Adenosine"],
        "vtms": ["Coal tar + Salicylic acid"],
        "vtms_excluded": ["Adenosine"],
    }


def test_from_params():
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
            "ntr_product_type": "generic",
            "ntr_form_route_ids": "1",
            "ntr_form_route_ids_excluded": "2",
            "ntr_ingredient_ids": "3",
            "ntr_ingredient_ids_excluded": "4",
            "ntr_vtm_ids": "5",
            "ntr_vtm_ids_excluded": "6",
        },
    )
    assert query == BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids=["1"],
        form_route_ids_excluded=["2"],
        ingredient_ids=["3"],
        ingredient_ids_excluded=["4"],
        vtm_ids=["5"],
        vtm_ids_excluded=["6"],
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
        form_route_ids_excluded=("2", "7"),
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
        "ntr_form_route_ids": "1,6",
        "ntr_form_route_ids_excluded": "2,7",
    }


def test_to_params_with_ingredient_ids():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        ingredient_ids=("1",),
        ingredient_ids_excluded=("2",),
        vtm_ids=("3",),
        vtm_ids_excluded=("4",),
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
        "ntr_ingredient_ids": "1",
        "ntr_ingredient_ids_excluded": "2",
        "ntr_vtm_ids": "3",
        "ntr_vtm_ids_excluded": "4",
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
def test_from_dict_form_route(dmd_data):
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
def test_from_dict_separate_form_route(dmd_data):
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
def test_get_form_route_ids_for_forms_and_routes(dmd_data):
    route_ids = _get_form_route_ids_for_forms_and_routes(
        form_routes=[], forms=["tablet"], routes=["oral"]
    )
    expected_route_ids = ["1"]

    assert route_ids == expected_route_ids


def test_get_form_route_ids_for_no_forms_or_routes():
    route_ids = _get_form_route_ids_for_forms_and_routes(
        form_routes=[], forms=[], routes=[]
    )
    expected_route_ids = []

    assert route_ids == expected_route_ids


@pytest.mark.django_db(databases=["data"], transaction=True)
def test_get_form_route_ids_for_invalid_form_routes(dmd_data):
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
