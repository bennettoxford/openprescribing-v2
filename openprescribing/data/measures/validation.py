from typing import Literal, Self

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

from openprescribing.data.models.dmd import OntFormRoute


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


class BNFCode(BaseModel):
    included: list[str]
    excluded: list[str] | None = None


class BNFQuery(BaseModel):
    bnf_codes: BNFCode | None = None
    form_routes: list[str] | None = None
    forms: list[str] | None = None
    routes: list[str] | None = None
    product_type: Literal["all", "generic", "branded"] = "all"
    ingredient_ids: list[int] | None = None

    @field_validator("form_routes")
    @classmethod
    def form_routes_must_be_valid(cls, v):
        valid_form_route_names = [fr.descr for fr in OntFormRoute.objects.all()]

        for fr in v:
            if fr not in valid_form_route_names:
                raise ValueError(f"Invalid form_route specified {fr}")
        return v

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


output_types = Literal["items"]


class Output(BaseModel):
    numerator: output_types
    denominator: output_types | Literal["list_size"]


class Measure(BaseModel):
    metadata: Metadata
    output: Output
    queries: list[Query]

    @field_validator("queries")
    @classmethod
    def only_one_query(cls, v):
        if v and len(v) > 1:
            raise ValueError("only one simultaneous query is currently supported")

    @model_validator(mode="after")
    def check_output_matches_query_structure(self) -> Self:
        if self.output.denominator == "list_size":
            if any(q.denominator for q in self.queries):
                raise ValueError(
                    "Should not specify any denominators with output_type `list_size`"
                )
        if self.output.denominator == "items":
            if not all(q.denominator for q in self.queries):
                raise ValueError(
                    "Must specify all denominators with output_type `items`"
                )


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
