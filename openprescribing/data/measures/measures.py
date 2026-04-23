from pathlib import Path

from strictyaml import (
    Any,
    Int,
    Map,
    MapCombined,
    Optional,
    Seq,
    Str,
    YAMLValidationError,
    load,
)


MEASURE_DEFINITIONS_PATH = Path(__file__).parents[3] / "measure_definitions"


class MeasureValidationError(Exception):
    def __init__(self, measure_name, validation_error):
        self.measure_name = measure_name
        self.validation_error = validation_error
        super().__init__()

    def __str__(self):
        return (
            f"Measure '{self.measure_name}' failed to validate: {self.validation_error}"
        )


def load_measure(measure_name, measures_path=MEASURE_DEFINITIONS_PATH):
    with open(measures_path / f"{measure_name}.yaml") as f:
        try:
            measure_yaml = load(f.read(), schema())
        except YAMLValidationError as e:
            raise MeasureValidationError(measure_name, e) from e

    # Return a dict rather than strictyaml's `YAML` - this would continue
    # to apply validation & we don't necessarily want that (e.g. `org_id`)
    return measure_yaml.data


def all_measure_details():
    measure_names = [f.stem for f in MEASURE_DEFINITIONS_PATH.iterdir()]
    measure_details = [
        {"name": f, "title": load_measure(f)["metadata"]["title"]}
        for f in measure_names
    ]
    return measure_details


# At the time of writing, this schema only validates measure features which have
# been implemented.
def schema():

    NUMERATOR_KEY = "numerator"
    DENOMINATOR_KEY = "denominator"

    # Require the specified keys, but also accept any other keys
    metadata = MapCombined(
        {
            "title": Str(),
            "tags": Seq(Str()),
            "why_it_matters": Str(),
        },
        Str(),
        Any(),
    )

    # nb. schema does not validate this is a valid BNF code
    bnf_code = Str()
    bnf_code_list = Seq(bnf_code)
    bnf_codes = Map(
        {
            Optional("included"): bnf_code_list,
            Optional("excluded"): bnf_code_list,
        }
    )
    # all of these query params are ANDed together
    query_params = Map(
        {
            Optional("bnf_codes"): bnf_codes,
            # corresponds to `cd` in `Ing`
            Optional("ingredient_ids"): Seq(Int()),
            # from a set list like `tablet`
            Optional("forms"): Seq(Str()),
            # can be `all`, `generic` or `branded`
            Optional("product_type"): Str(),
            # from a set list like `oral`
            Optional("routes"): Seq(Str()),
            # from a set list like `tablet.oral`
            Optional("form_routes"): Seq(Str()),
        }
    )
    # Currently this must be `items` or `list_size`
    output = Str()
    query = Map(
        {
            NUMERATOR_KEY: query_params,
            Optional(DENOMINATOR_KEY): query_params,
        }
    )
    schema = Map(
        {
            "metadata": metadata,
            "output": Map({NUMERATOR_KEY: output, DENOMINATOR_KEY: output}),
            "queries": Seq(query),
        }
    )

    return schema
