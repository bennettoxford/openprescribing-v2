from openprescribing.data.measures import load_measure


def test_load_measure():
    m = load_measure("detemir")
    assert m == {
        "metadata": {
            "title": "Insulin detemir",
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
