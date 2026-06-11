from typing import Literal

from pydantic import BaseModel, field_validator, model_validator
from pydantic_core import ValidationError
from strictyaml import (
    Any,
    Int,
    Map,
    MapCombined,
    Optional,
    Seq,
    Str,
)


class MeasureValidationError(Exception):
    def __init__(self, measure_name, validation_error):
        self.measure_name = measure_name
        self.validation_error = validation_error
        super().__init__()

    def __str__(self):
        return (
            f"Measure '{self.measure_name}' failed to validate: {self.validation_error}"
        )


class Metadata(BaseModel):
    title: str
    tags: list[str]
    why_it_matters: str


class BNFQuery(BaseModel):
    bnf_codes: list[str] | None = None
    bnf_codes_excluded: list[str] | None = None
    form_routes: list[str] | None = None
    forms: list[str] | None = None
    routes: list[str] | None = None
    product_type: Literal["all", "generic", "branded"] = "all"
    ingredient_ids: list[int] | None = None

    @model_validator(mode="after")
    def check_xor_form_routes_forms_routes(self) -> "BNFQuery":
        if self.form_routes:
            if self.forms or self.routes:
                raise ValueError(
                    "`form_routes` cannot be used at the same time as `forms` or `routes`"
                )
        return self


class Query(BaseModel):
    numerator: BNFQuery
    denominator: BNFQuery | None = None


output_values = (
    Literal["items"] | Literal["quantity"] | Literal["cost"] | Literal["custom"]
)

analysis_types = (
    Literal["prescribing_vs_prescribing"] | Literal["prescribing_vs_list_size"]
)


class Options(BaseModel):
    type: analysis_types
    output_value: output_values


class Measure(BaseModel):
    metadata: Metadata
    options: Options
    queries: list[Query]

    @field_validator("queries")
    @classmethod
    def only_one_query(cls, v):
        if v and len(v) > 1:
            raise ValueError("only one simultaneous query is currently supported")


def validate_dict(measure_name, measure_dict):
    try:
        Measure.model_validate(measure_dict)
    except ValidationError as e:
        raise MeasureValidationError(measure_name, e) from e


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
    # all of these query params are ANDed together
    query_params = Map(
        {
            Optional("bnf_codes"): bnf_code_list,
            Optional("bnf_codes_excluded"): bnf_code_list,
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
    # Currently this must be `items`, `quantity`, `cost`, or `custom`.
    output_values = Str()
    # Currently this must be `prescribing_vs_prescribing` or `prescribing_vs_list_size`
    analysis_types = Str()

    query = Map(
        {
            NUMERATOR_KEY: query_params,
            Optional(DENOMINATOR_KEY): query_params,
        }
    )
    schema = Map(
        {
            "metadata": metadata,
            "options": Map({"type": analysis_types, "output_value": output_values}),
            "queries": Seq(query),
        }
    )

    return schema
