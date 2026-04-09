from pathlib import Path

import yaml


MEASURE_DEFINITIONS_PATH = Path(__file__).parents[3] / "measure_definitions"


def load_measure(measure_name):
    with open(MEASURE_DEFINITIONS_PATH / f"{measure_name}.yaml") as f:
        measure_yaml = yaml.safe_load(f)
    return measure_yaml


def all_measure_details():
    measure_names = [f.stem for f in MEASURE_DEFINITIONS_PATH.iterdir()]
    measure_details = [
        {"name": f, "title": load_measure(f)["metadata"]["title"]}
        for f in measure_names
    ]
    return measure_details


# TODO
def validate_measure(measure_name):  # pragma: no cover
    return True
