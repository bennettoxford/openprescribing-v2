from pathlib import Path

import yaml


def load_measure(measure_name):
    with open(Path(__file__).parent / "definitions" / f"{measure_name}.yaml") as f:
        measure_yaml = yaml.safe_load(f)
    return measure_yaml


# TODO
def validate_measure(measure_name):  # pragma: no cover
    return True
