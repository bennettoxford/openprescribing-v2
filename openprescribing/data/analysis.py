from __future__ import annotations

from dataclasses import dataclass

from .bnf_query import BNFQuery, MultiBNFQuery
from .list_size_query import ListSizeQuery


@dataclass
class AnalysisQuery:
    """Represents a numerator/denominator pair as part of an Analysis"""

    ntr_query: BNFQuery
    dtr_query: BNFQuery | ListSizeQuery


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

    # This is a tuple rather than a list so that it is hashable, so that we
    # can use functools.lru_cache for get_practice_date_matrix()
    queries: tuple[AnalysisQuery]
    org_id: str | None

    @property
    def ntr_query(self):
        if len(self.queries) == 1:
            return self.queries[0].ntr_query
        assert all(isinstance(q.ntr_query, BNFQuery) for q in self.queries)
        return MultiBNFQuery(tuple([q.ntr_query for q in self.queries]))

    @property
    def dtr_query(self):
        if len(self.queries) == 1:
            return self.queries[0].dtr_query
        assert all(
            isinstance(q.dtr_query, BNFQuery) or isinstance(q.dtr_query, ListSizeQuery)
            for q in self.queries
        )
        return MultiBNFQuery.from_list([q.dtr_query for q in self.queries])

    @classmethod
    def from_params(cls, params):
        """Build an Analysis from URL query parameters."""

        ntr_query = BNFQuery.from_params("ntr", params)

        if BNFQuery.has_params("dtr", params):
            dtr_query = BNFQuery.from_params("dtr", params)
        else:
            dtr_query = ListSizeQuery()

        org_id = params.get("org_id")
        queries = (AnalysisQuery(ntr_query, dtr_query),)

        return cls(
            queries=queries,
            org_id=org_id,
        )

    def to_params(self):
        """Serialize back to URL query parameters."""

        assert len(self.queries) == 1
        params = {}
        params.update(self.ntr_query.to_params("ntr"))
        params.update(self.dtr_query.to_params("dtr"))
        if self.org_id:
            params["org_id"] = self.org_id
        return params

    @classmethod
    def from_dict(cls, analysis_dict):
        query_list = []
        for query in analysis_dict["queries"]:
            ntr_query = BNFQuery.from_dict(query["numerator"])

            if "denominator" in query:
                dtr_query = BNFQuery.from_dict(query["denominator"])
            else:
                dtr_query = ListSizeQuery()
            query_list.append(AnalysisQuery(ntr_query, dtr_query))

        return cls(
            queries=tuple(query_list),
            org_id=analysis_dict.get("org_id"),
        )

    def to_dict(self):
        analysis_dict = {"queries": []}

        for query in self.queries:
            new_query = {"numerator": query.ntr_query.to_dict()}
            if not isinstance(query.dtr_query, ListSizeQuery):
                new_query["denominator"] = query.dtr_query.to_dict()
            analysis_dict["queries"].append(new_query)

        if self.org_id:
            analysis_dict["org_id"] = self.org_id

        return analysis_dict
