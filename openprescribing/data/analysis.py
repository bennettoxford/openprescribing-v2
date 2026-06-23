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

    def validate(self):
        """Validate the analysis's BNF queries, raising ValueError if invalid."""

        self.ntr_query.validate()
        if isinstance(self.dtr_query, BNFQuery):
            self.dtr_query.validate()

    @classmethod
    def from_dict(cls, analysis_dict):
        assert len(analysis_dict["queries"]) == 1, (
            "We only currently support one numerator/denominator pair"
        )

        numerator = analysis_dict["queries"][0]["numerator"]
        ntr_query = BNFQuery.from_dict(numerator)

        if "denominator" in analysis_dict["queries"][0]:
            denominator = analysis_dict["queries"][0]["denominator"]
            dtr_query = BNFQuery.from_dict(denominator)
        else:
            dtr_query = ListSizeQuery()

        return cls(
            ntr_query=ntr_query,
            dtr_query=dtr_query,
            org_id=analysis_dict.get("org_id"),
        )

    def to_dict(self):
        analysis_dict = {"options": {}, "queries": []}

        analysis_dict["queries"].append({"numerator": self.ntr_query.to_dict()})
        analysis_dict["options"]["output_value"] = "items"

        if isinstance(self.dtr_query, ListSizeQuery):
            analysis_dict["options"]["type"] = "prescribing_vs_list_size"
        else:
            analysis_dict["queries"][0]["denominator"] = self.dtr_query.to_dict()
            analysis_dict["options"]["type"] = "prescribing_vs_prescribing"

        if self.org_id:
            analysis_dict["org_id"] = self.org_id

        return analysis_dict
