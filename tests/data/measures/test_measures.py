from pathlib import Path

import pytest

from openprescribing.data.measures import load_measure, measures
from tests.utils.ingest_utils import ingest_dmd_data


def test_load_measure():
    m = load_measure("detemir")
    assert m == {
        "metadata": {
            "tags": [
                "demo",
            ],
            "title": "Insulin detemir",
            "why_it_matters": "Novo Nordisk are [discontinuing all formulations of "
            "Levemir®](https://www.diabetes.org.uk/about-us/news-and-views/novo-nordisk-to-withdraw-levemir-what-you-need-to-know), "
            "the only insulin detemir product available in the UK, with supply due "
            "to exhaust by December 2026.\n"
            "The Primary Care Diabetes & Obesity Society (PCDOS) and Association "
            "of British Clinical Diabetologists (ABCD) have [written "
            "guidance](https://cms.pcdosociety.org/uploads/Levemir_Discontinuation_Guideline_Final_110825_17d277acd3.pdf) "
            "to support clinicians in selecting and safely initiating alternative "
            "basal insulins. The guidance recommends that local teams diversify "
            "prescribing across the available options to reduce supply risks. "
            "Given the significant regional variation in prescribing, it also "
            "advises using data to support planning.\n"
            "This OpenPrescribing measure, alongside it’s [OpenPrescribing "
            "Hospitals "
            "counterpart](https://hospitals.openprescribing.net/measures/insulin_detemir/) "
            "provides data on variation across primary and secondary care to "
            "support this planning.\n",
        },
        "output": {
            "denominator": "list_size",
            "numerator": "items",
        },
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": [
                            "0601012X0",
                        ],
                    },
                },
            },
        ],
    }


def test_load_measure_strictyaml_validation_invalid(settings):
    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    with pytest.raises(measures.MeasureValidationError) as excinfo:
        load_measure("invalid-measure-queries")
    assert "'invalid-measure-queries' failed to validate" in str(excinfo.value)


@pytest.mark.parametrize(
    "measure_name,key,value",
    [
        ("valid-measure", "form_routes", "tablet.oral"),
        ("valid-measure-multiple-queries", "forms", "tablet"),
        ("valid-measure-multiple-queries-denominator", "forms", "tablet"),
    ],
)
@pytest.mark.django_db(databases=["data"], transaction=True)
def test_load_measure_pydantic_validation_valid_form_route(
    rxdb, settings, tmp_path, measure_name, key, value
):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    m = load_measure(measure_name)
    assert value in m["queries"][0]["numerator"][key]


@pytest.mark.parametrize(
    "measure_name",
    [
        "invalid-measure-form_routes",
        "invalid-measure-form_routes-and-routes",
        "invalid-measure-multiple-queries-output-items",
        "invalid-measure-multiple-queries-output-list_size",
        "invalid-measure-output",
        "invalid-measure-product-type",
    ],
)
@pytest.mark.django_db(databases=["data"], transaction=True)
def test_load_measure_pydantic_validation_invalid_measure(
    rxdb, settings, tmp_path, measure_name
):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    with pytest.raises(measures.MeasureValidationError) as excinfo:
        load_measure(measure_name)
    assert f"'{measure_name}' failed to validate" in str(excinfo.value)
