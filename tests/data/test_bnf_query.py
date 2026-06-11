from openprescribing.data.bnf_query import (
    BNFQuery,
    ProductType,
    _expand_forms_and_routes,
)


def test_init_normalizes_lists_to_tuples():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_routes=["tablet.oral", "suspension.oral"],
        form_routes_excluded=["solutioninjection.intravenous"],
        forms=["tablet"],
        forms_excluded=["capsule"],
        routes=["oral"],
        routes_excluded=["intravenous"],
        ingredient_ids=[2],
        ingredient_ids_excluded=[3],
        vtm_ids=[4],
        vtm_ids_excluded=[5],
    )
    assert query == BNFQuery(
        bnf_codes=("01",),
        bnf_codes_excluded=("0101",),
        product_type=ProductType.GENERIC,
        form_routes=("tablet.oral", "suspension.oral"),
        form_routes_excluded=("solutioninjection.intravenous",),
        forms=("tablet",),
        forms_excluded=("capsule",),
        routes=("oral",),
        routes_excluded=("intravenous",),
        ingredient_ids=(2,),
        ingredient_ids_excluded=(3,),
        vtm_ids=(4,),
        vtm_ids_excluded=(5,),
    )


def test_get_matching_presentation_codes(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0AA", "1001030U0BD"], bnf_codes_excluded=["1001030U0AAABAB"]
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_no_excludes(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0AA"])
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


def test_get_matching_presentation_codes_for_strength_and_formulation(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0_AC"])
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_for_generic(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


def test_get_matching_presentation_codes_for_generic_with_strength_and_formulation(
    medications,
):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0_AB"], product_type=ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
    ]


def test_get_matching_presentation_codes_for_branded(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_for_branded_with_strength_and_formulation(
    medications,
):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(bnf_codes=["1001030U0_AB"], product_type=ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
    ]


def test_get_matching_presentation_codes_for_form_routes(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "0203020C0AAAAAA",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "0203020C0AAAAAA",
            "ntr_form_routes": "solutioninjection.intravenous",
        },
    )
    assert query.get_matching_presentation_codes() == ["0203020C0AAAAAA"]


def test_get_matching_presentation_codes_for_ingredient_ids(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1305020C0AAFVFV",
                "ingredient_ids": [387253001, 3588411000001101],
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "ingredient_ids": [387253001, 3588411000001101],
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "ingredient_ids": [387253001, 53034005],
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "ingredient_ids": [387253001, 53034005],
            },
        ]
    )
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_ingredient_ids": "53034005",
        },
    )
    assert query.get_matching_presentation_codes() == ["1305020C0AAFVFV"]


def test_get_matching_presentation_codes_for_ingredient_ids_no_match(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1305020C0AAFVFV",
                "ingredient_ids": [387253001, 3588411000001101],
            },
        ]
    )
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_ingredient_ids": "999",
        },
    )
    assert query.get_matching_presentation_codes() == []


def test_get_matching_presentation_codes_for_vtm_ids(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1305020C0AAFVFV",
                "vtm_id": 15219611000001105,
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "vtm_id": 15219611000001105,
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "vtm_id": 15219611000001105,
            },
            {
                "bnf_code": "1305020C0AAFVFV",
                "vtm_id": 15219611000001105,
            },
        ]
    )
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "1305020C0AAFVFV",
            "ntr_vtm_ids": "15219611000001105",
        },
    )
    assert query.get_matching_presentation_codes() == ["1305020C0AAFVFV"]


def test_get_matching_presentation_codes_for_vtm_ids_excluded(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB", "vtm_id": 90356005},
            {"bnf_code": "1001030U0AAACAC", "vtm_id": 90356005},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC"},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        vtm_ids_excluded=["90356005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_for_form_routes_excluded(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1001030U0AAABAB",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
            {
                "bnf_code": "1001030U0BDAAAB",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0BDABAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        form_routes_excluded=["solutioninjection.intravenous"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_for_form_routes_include_and_exclude(
    medications,
):
    medications.add_rows(
        [
            {
                "bnf_code": "1001030U0AAABAB",
                "form_routes": ["tablet.oral", "solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
            {
                "bnf_code": "1001030U0BDAAAB",
                "form_routes": ["tablet.oral", "solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0BDABAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        form_routes=["tablet.oral"],
        form_routes_excluded=["solutioninjection.intravenous"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


def test_get_matching_presentation_codes_for_forms(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "0203020C0AAAAAA",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["0203020C0AAAAAA", "1001030U0AAACAC"],
        forms=["tablet"],
    )
    assert query.get_matching_presentation_codes() == ["1001030U0AAACAC"]


def test_get_matching_presentation_codes_for_routes(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "0203020C0AAAAAA",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["0203020C0AAAAAA", "1001030U0AAACAC"],
        routes=["oral"],
    )
    assert query.get_matching_presentation_codes() == ["1001030U0AAACAC"]


def test_get_matching_presentation_codes_for_routes_excluded(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1001030U0AAABAB",
                "form_routes": ["solutioninjection.intravenous"],
            },
            {"bnf_code": "1001030U0AAACAC", "form_routes": ["tablet.oral"]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        routes_excluded=["oral"],
    )
    assert query.get_matching_presentation_codes() == ["1001030U0AAABAB"]


def test_get_matching_presentation_codes_for_ingredient_ids_excluded(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC", "ingredient_ids": [53034005]},
            {"bnf_code": "1001030U0BDAAAB"},
            {"bnf_code": "1001030U0BDABAC", "ingredient_ids": [53034005]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0BDAAAB",
    ]


def test_get_matching_presentation_codes_for_ingredient_ids_include_and_exclude(
    medications,
):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0AAACAC", "ingredient_ids": [11111, 53034005]},
            {"bnf_code": "1001030U0BDAAAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0BDABAC", "ingredient_ids": [11111, 53034005]},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        ingredient_ids=["11111"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0BDAAAB",
    ]


def test_get_matching_presentation_codes_for_ingredient_ids_excluded_no_match(
    medications,
):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB"},
            {"bnf_code": "1001030U0AAACAC"},
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0AA"],
        ingredient_ids_excluded=["999"],
    )
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


def test_get_matching_presentation_codes_with_combined_exclusions(medications):
    medications.add_rows(
        [
            {
                "bnf_code": "1001030U0AAABAB",
                "form_routes": ["tablet.oral", "solutioninjection.intravenous"],
                "ingredient_ids": [11111],
            },
            {
                "bnf_code": "1001030U0AAACAC",
                "form_routes": ["tablet.oral"],
                "ingredient_ids": [11111],
            },
            {
                "bnf_code": "1001030U0BDAAAB",
                "form_routes": ["tablet.oral", "solutioninjection.intravenous"],
                "ingredient_ids": [11111],
            },
            {
                "bnf_code": "1001030U0BDABAC",
                "form_routes": ["tablet.oral"],
                "ingredient_ids": [11111, 53034005],
            },
        ]
    )
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        bnf_codes_excluded=["1001030U0AAABAB"],
        form_routes=["tablet.oral"],
        form_routes_excluded=["solutioninjection.intravenous"],
        ingredient_ids=["11111"],
        ingredient_ids_excluded=["53034005"],
    )
    assert query.get_matching_presentation_codes() == ["1001030U0AAACAC"]


def test_describe_search_for_all_product_types(bnf_codes):
    query = BNFQuery(bnf_codes=["1001030U0"], bnf_codes_excluded=["1001030U0_AB"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": ["Methotrexate"],
        "bnf_codes_excluded": ["Methotrexate 2.5mg tablets (branded and generic)"],
        "form_routes": [],
        "form_routes_excluded": [],
        "forms": [],
        "forms_excluded": [],
        "routes": [],
        "routes_excluded": [],
        "ingredients": [],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


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
        "forms": [],
        "forms_excluded": [],
        "routes": [],
        "routes_excluded": [],
        "ingredients": [],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


def test_describe_search_for_ingredients(dmd_data):
    query = BNFQuery(bnf_codes=[], ingredient_ids=["53034005"])
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": [],
        "bnf_codes_excluded": [],
        "form_routes": [],
        "form_routes_excluded": [],
        "forms": [],
        "forms_excluded": [],
        "routes": [],
        "routes_excluded": [],
        "ingredients": ["Coal tar"],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


def test_describe_search_for_all_filter_types(dmd_data, bnf_codes):
    query = BNFQuery(
        bnf_codes=["1001030U0"],
        bnf_codes_excluded=["1001030U0_AB"],
        form_routes=["suspension.oral"],
        form_routes_excluded=["solution.oral"],
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
        "forms": [],
        "forms_excluded": [],
        "routes": [],
        "routes_excluded": [],
        "ingredients": ["Coal tar"],
        "ingredients_excluded": ["Adenosine"],
        "vtms": ["Coal tar + Salicylic acid"],
        "vtms_excluded": ["Adenosine"],
    }


def test_describe_search_for_forms_and_routes():
    query = BNFQuery(
        forms=["tablet"],
        forms_excluded=["capsule"],
        routes=["oral"],
        routes_excluded=["intravenous"],
    )
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "bnf_codes": [],
        "bnf_codes_excluded": [],
        "form_routes": [],
        "form_routes_excluded": [],
        "forms": ["tablet"],
        "forms_excluded": ["capsule"],
        "routes": ["oral"],
        "routes_excluded": ["intravenous"],
        "ingredients": [],
        "ingredients_excluded": [],
        "vtms": [],
        "vtms_excluded": [],
    }


def test_from_params():
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
            "ntr_product_type": "generic",
            "ntr_form_routes": "tablet.oral",
            "ntr_form_routes_excluded": "solution.oral",
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
        form_routes=["tablet.oral"],
        form_routes_excluded=["solution.oral"],
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


def test_from_params_with_form_routes_key_not_val():
    query = BNFQuery.from_params(
        "ntr",
        {
            "ntr_bnf_codes": "01",
            "ntr_product_type": "generic",
            "ntr_form_routes": "",
        },
    )
    assert query.form_routes == ()


def test_from_params_ingredients():
    query = BNFQuery.from_params("ntr", {"ntr_ingredient_ids": "01"})
    assert query == BNFQuery(
        bnf_codes=[], product_type=BNFQuery.PRODUCT_TYPE_DEFAULT, ingredient_ids=["01"]
    )


def test_to_params():
    query = BNFQuery(bnf_codes=["01"])
    assert query.to_params("ntr") == {"ntr_bnf_codes": "01", "ntr_product_type": "all"}


def test_to_params_excluded():
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


def test_to_params_with_form_routes():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_routes=("tablet.oral", "suspension.oral"),
        form_routes_excluded=("solution.oral", "ointment.cutaneous"),
    )
    assert query.to_params("ntr") == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "generic",
        "ntr_form_routes": "tablet.oral,suspension.oral",
        "ntr_form_routes_excluded": "solution.oral,ointment.cutaneous",
    }


def test_to_params_with_ingredient_ids():
    query = BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        ingredient_ids=(1,),
        ingredient_ids_excluded=(2,),
        vtm_ids=(3,),
        vtm_ids_excluded=(4,),
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


def test_to_dict_bnf_codes_included():
    query = BNFQuery(bnf_codes=["1001030U0"])
    assert query.to_dict() == {"bnf_codes": {"included": ["1001030U0"]}}


def test_to_dict_bnf_codes_excluded():
    query = BNFQuery(bnf_codes=["1001030U0"], bnf_codes_excluded=["1001030U0AAABAB"])
    assert query.to_dict() == {
        "bnf_codes": {
            "included": ["1001030U0"],
            "excluded": ["1001030U0AAABAB"],
        }
    }


def test_to_dict_product_type():
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.GENERIC)
    assert query.to_dict() == {
        "bnf_codes": {"included": ["1001030U0"]},
        "product_type": "generic",
    }


def test_to_dict_product_type_all_omitted():
    query = BNFQuery(bnf_codes=["1001030U0"], product_type=ProductType.ALL)
    assert query.to_dict() == {"bnf_codes": {"included": ["1001030U0"]}}


def test_to_dict_form_routes():
    query = BNFQuery(form_routes=["tablet.oral"])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "form_routes": ["tablet.oral"],
    }


def test_to_dict_form_routes_excluded():
    query = BNFQuery(form_routes_excluded=["solutioninjection.intravenous"])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "form_routes_excluded": ["solutioninjection.intravenous"],
    }


def test_to_dict_forms_and_routes():
    query = BNFQuery(
        forms=["tablet"],
        forms_excluded=["capsule"],
        routes=["oral"],
        routes_excluded=["intravenous"],
    )
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "forms": ["tablet"],
        "forms_excluded": ["capsule"],
        "routes": ["oral"],
        "routes_excluded": ["intravenous"],
    }


def test_to_dict_ingredient_ids():
    query = BNFQuery(ingredient_ids=[53034005])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "ingredient_ids": [53034005],
    }


def test_to_dict_ingredient_ids_excluded():
    query = BNFQuery(ingredient_ids_excluded=[53034005])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "ingredient_ids_excluded": [53034005],
    }


def test_to_dict_vtm_ids():
    query = BNFQuery(vtm_ids=[15219611000001105])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "vtm_ids": [15219611000001105],
    }


def test_to_dict_vtm_ids_excluded():
    query = BNFQuery(vtm_ids_excluded=[108502004])
    assert query.to_dict() == {
        "bnf_codes": {"included": []},
        "vtm_ids_excluded": [108502004],
    }


def test_from_dict_bnf_codes_included():
    query = BNFQuery.from_dict({"bnf_codes": {"included": ["1001030U0"]}})
    assert query == BNFQuery(bnf_codes=["1001030U0"])


def test_from_dict_bnf_codes_excluded():
    query = BNFQuery.from_dict(
        {"bnf_codes": {"included": ["1001030U0"], "excluded": ["1001030U0AAABAB"]}}
    )
    assert query == BNFQuery(
        bnf_codes=["1001030U0"], bnf_codes_excluded=["1001030U0AAABAB"]
    )


def test_from_dict_product_type():
    query = BNFQuery.from_dict({"product_type": "generic"})
    assert query == BNFQuery(product_type=ProductType.GENERIC)


def test_from_dict_form_routes():
    query = BNFQuery.from_dict({"form_routes": ["tablet.oral"]})
    assert query == BNFQuery(form_routes=["tablet.oral"])


def test_from_dict_forms():
    query = BNFQuery.from_dict({"forms": ["pressurizedinhalation"]})
    assert query == BNFQuery(forms=["pressurizedinhalation"])


def test_from_dict_routes():
    query = BNFQuery.from_dict({"routes": ["subretinal"]})
    assert query == BNFQuery(routes=["subretinal"])


def test_from_dict_form_routes_excluded():
    query = BNFQuery.from_dict(
        {"form_routes_excluded": ["solutioninjection.intravenous"]}
    )
    assert query == BNFQuery(form_routes_excluded=["solutioninjection.intravenous"])


def test_from_dict_forms_excluded():
    query = BNFQuery.from_dict({"forms_excluded": ["pressurizedinhalation"]})
    assert query == BNFQuery(forms_excluded=["pressurizedinhalation"])


def test_from_dict_routes_excluded():
    query = BNFQuery.from_dict({"routes_excluded": ["subretinal"]})
    assert query == BNFQuery(routes_excluded=["subretinal"])


def test_from_dict_ingredient_ids():
    query = BNFQuery.from_dict({"ingredient_ids": [53034005]})
    assert query == BNFQuery(ingredient_ids=[53034005])


def test_from_dict_ingredient_ids_excluded():
    query = BNFQuery.from_dict({"ingredient_ids_excluded": [53034005]})
    assert query == BNFQuery(ingredient_ids_excluded=[53034005])


def test_from_dict_vtm_ids():
    query = BNFQuery.from_dict({"vtm_ids": [15219611000001105]})
    assert query == BNFQuery(vtm_ids=[15219611000001105])


def test_from_dict_vtm_ids_excluded():
    query = BNFQuery.from_dict({"vtm_ids_excluded": [108502004]})
    assert query == BNFQuery(vtm_ids_excluded=[108502004])


def test_from_dict_form_route():
    test_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "form_routes": ["solutioninjection.intravenous"],
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


def test_from_dict_form_route_excluded():
    test_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "form_routes": ["solutioninjection.intravenous"],
        "form_routes_excluded": ["suspension.oral"],
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


def test_from_dict_separate_form_route():
    # forms and routes are preserved as-is, rather than being expanded into form_routes.
    test_dict = {
        "bnf_codes": {
            "included": ["0203020C0AAAAAA"],
        },
        "forms": ["solutioninjection"],
        "routes": ["intravenous"],
    }
    query = BNFQuery.from_dict(test_dict)
    assert query.to_dict() == test_dict


def test_expand_forms_and_routes(dmd_data):
    # A form matches descriptions starting `{form}.`, a route those ending `.{route}`,
    # and when both are given a description must match all of them.
    assert _expand_forms_and_routes(forms=["tablet"], routes=["oral"]) == [
        "tablet.oral"
    ]


def test_expand_no_forms_or_routes():
    assert _expand_forms_and_routes(forms=[], routes=[]) == []


def test_expand_unknown_forms_and_routes(dmd_data):
    # Unknown forms or routes match nothing rather than raising.
    assert _expand_forms_and_routes(forms=["unicorn"], routes=[]) == []
    assert _expand_forms_and_routes(forms=[], routes=["interstellar"]) == []
