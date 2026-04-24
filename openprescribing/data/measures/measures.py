from django.conf import settings
from strictyaml import (
    YAMLValidationError,
    load,
)

from .validation import MeasureValidationError, schema


def load_measure(measure_name):
    with open(settings.MEASURE_DEFINITIONS_PATH / f"{measure_name}.yaml") as f:
        try:
            # Take forward a dict rather than strictyaml's `YAML` - this would continue
            # to apply validation & we don't necessarily want that (e.g. `org_id`)
            measure_dict = load(f.read(), schema()).data
        except YAMLValidationError as e:
            raise MeasureValidationError(measure_name, e) from e

    return measure_dict


def all_measure_details():
    measure_names = [f.stem for f in settings.MEASURE_DEFINITIONS_PATH.iterdir()]
    measure_details = []
    for f in measure_names:
        measure = load_measure(f)
        measure_details.append(
            {
                "name": f,
                "title": measure["metadata"]["title"],
                "tags": measure["metadata"]["tags"],
            }
        )
    return measure_details
