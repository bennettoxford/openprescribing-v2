from pathlib import Path

import pytest

from openprescribing.data.measures import load_measure, measures
from tests.utils.ingest_utils import ingest_dmd_data


def test_load_measure(settings):
    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    m = load_measure("demo-branded-ratio")
    assert m == {
        "metadata": {
            "tags": [
                "demo",
            ],
            "title": "DEMO Ratio of branded prescribing of a drug to all prescribing of a drug",
            "why_it_matters": "This one doesn't really matter!",
        },
        "options": {
            "type": "prescribing_vs_prescribing",
            "output_value": "items",
        },
        "queries": [
            {
                "numerator": {
                    "bnf_codes": [
                        "0302000K0",
                    ],
                    "product_type": "branded",
                },
                "denominator": {
                    "bnf_codes": [
                        "0302000K0",
                    ],
                    "product_type": "all",
                },
            },
        ],
    }


def test_load_measure_strictyaml_validation_invalid(settings):
    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    with pytest.raises(measures.MeasureValidationError) as excinfo:
        load_measure("invalid-measure-queries")
    assert "'invalid-measure-queries' failed to validate" in str(excinfo.value)


def test_load_measure_pydantic_validation_valid_form_route(rxdb, settings, tmp_path):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    m = load_measure("valid-measure")
    assert "tablet.oral" in m["queries"][0]["numerator"]["form_routes"]


@pytest.mark.parametrize(
    "measure_name",
    [
        "invalid-measure-form_routes-and-routes",
        "invalid-measure-multiple-queries",
        "invalid-measure-output",
        "invalid-measure-product-type",
    ],
)
def test_load_measure_pydantic_validation_invalid_measure(
    rxdb, settings, tmp_path, measure_name
):
    rxdb.ingest([{}])
    ingest_dmd_data(settings, tmp_path)

    settings.MEASURE_DEFINITIONS_PATH = Path(__file__).parent / "fixtures"
    with pytest.raises(measures.MeasureValidationError) as excinfo:
        load_measure(measure_name)
    assert f"'{measure_name}' failed to validate" in str(excinfo.value)
