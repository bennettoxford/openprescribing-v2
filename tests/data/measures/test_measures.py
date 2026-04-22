from pathlib import Path

import pytest

from openprescribing.data.measures import load_measure, measures


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
            "numerator": "bnf_items",
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


def test_load_measure_validation_fail():
    with pytest.raises(measures.MeasureValidationError) as excinfo:
        load_measure(
            "invalid-measure", measures_path=Path(__file__).parent / "fixtures"
        )
    assert "'invalid-measure' failed to validate" in str(excinfo.value)
