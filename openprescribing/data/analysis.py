from __future__ import annotations

from dataclasses import dataclass

from .bnf_query import BNFQuery
from .list_size_query import ListSizeQuery


@dataclass
class Analysis:
    """Represents a prescribing analysis.

    A prescribing analysis computes the ratio of either:

    * (the number of items prescribed matching a BNF query) to (the number of items
    prescribed matching another BNF query), or
    * (the number of items prescribed matching a BNF query) to (the number of patients / 1000)

    for each organisation of a given type, for each month.  By default, analyses are for
    ICBs, unless a particular organisation is selected, in which case that
    organisation's type is used.

    There is a related class, AnalysisPresentation, that holds configuration for
    displaying a prescribing analysis.  When new options are added to the UI, fields
    should be added to this class if they are required by the API, and to
    AnalysisPresentation if they are not.
    """

    ntr_query: BNFQuery
    dtr_query: BNFQuery | ListSizeQuery
    org_id: str | None

    @classmethod
    def from_params(cls, params):
        """Build an Analysis from URL query parameters."""

        ntr_query = BNFQuery.from_params("ntr", params)

        if params.get("dtr_codes"):
            dtr_query = BNFQuery.from_params("dtr", params)
        else:
            dtr_query = ListSizeQuery()

        org_id = params.get("org_id")

        return cls(
            ntr_query=ntr_query,
            dtr_query=dtr_query,
            org_id=org_id,
        )

    def to_params(self):
        """Serialize back to URL query parameters."""

        params = {}
        params.update(self.ntr_query.to_params("ntr"))
        params.update(self.dtr_query.to_params("dtr"))
        if self.org_id:
            params["org_id"] = self.org_id
        return params

    @classmethod
    def from_dict(cls, analysis_dict):
        assert len(analysis_dict["queries"]) == 1, (
            "We only currently support one numerator/denominator pair"
        )

        numerator = analysis_dict["queries"][0]["numerator"]
        numerator_bnf_codes = numerator["bnf_codes"]
        if "product_type" in numerator:
            numerator_bnf_codes["product_type"] = numerator["product_type"]
        ntr_query = BNFQuery.from_dict(numerator_bnf_codes)

        if "denominator" in analysis_dict["queries"][0]:
            denominator = analysis_dict["queries"][0]["denominator"]
            denominator_bnf_codes = denominator["bnf_codes"]
            if "product_type" in denominator:
                denominator_bnf_codes["product_type"] = denominator["product_type"]
            dtr_query = BNFQuery.from_dict(denominator_bnf_codes)
        else:
            dtr_query = ListSizeQuery()

        return cls(
            ntr_query=ntr_query,
            dtr_query=dtr_query,
            org_id=analysis_dict.get("org_id"),
        )
