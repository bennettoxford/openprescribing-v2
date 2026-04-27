from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import reduce
from operator import and_

from django.db.models import Q

from openprescribing.data import rxdb
from openprescribing.data.models.dmd import Ing, OntFormRoute

from .models import BNFCode


class ProductType(StrEnum):
    ALL = "all"
    GENERIC = "generic"
    BRANDED = "branded"


def _get_bnf_codes_for_form_route_ids(form_route_ids):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            f"""
            SELECT bnf_code
            FROM medications
            WHERE list_has_any(form_route_ids, [{", ".join(form_route_ids)}])
            """
        )
        return [x[0] for x in results.fetchall()]


def _get_form_route_ids_for_forms_and_routes(form_routes, forms, routes):
    query = Q()
    if form_routes:
        assert not routes and not forms, (
            "We do not currently support mixing form_routes with routes / forms individually"
        )
        query = Q(descr__in=form_routes)
    else:
        conditions = []
        if routes:
            for route in routes:
                conditions.append(Q(descr__endswith=f".{route}"))
        if forms:
            for form in forms:
                conditions.append(Q(descr__startswith=f"{form}."))
        if conditions:
            query = reduce(and_, conditions)

    form_route_ids = [
        str(form_route.cd) for form_route in OntFormRoute.objects.filter(query)
    ]

    if not form_route_ids and (form_routes or routes or forms):
        raise ValueError(
            f"No matching form_routes for form_routes={form_routes}, routes={routes}, forms={forms}"
        )

    return form_route_ids


def _get_bnf_codes_for_ingredient_ids(ingredient_ids):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            f"""
            SELECT bnf_code
            FROM medications
            WHERE list_has_any(ingredient_ids, [{", ".join(ingredient_ids)}])
            """
        )
        return [x[0] for x in results.fetchall()]


@dataclass(frozen=True)
class BNFQuery:
    """Represents a query returning codes for BNF presentations."""

    terms: tuple[Term]
    product_type: ProductType = ProductType.ALL
    form_route_ids: tuple[str] = ()
    ingredient_ids: tuple[str] = ()

    PRODUCT_TYPE_DEFAULT = "all"

    @classmethod
    def build(cls, raw_terms, product_type="all", form_route_ids=(), ingredient_ids=()):
        return cls(
            tuple([Term.from_param_value(rt) for rt in raw_terms]),
            ProductType(product_type),
            tuple(form_route_ids),
            tuple(ingredient_ids),
        )

    @classmethod
    def from_params(cls, field, params):
        """Build a BNFQuery from URL query parameters for a field."""

        if params.get(f"{field}_codes", ""):
            raw_terms = tuple(params[f"{field}_codes"].split(","))
        else:
            raw_terms = ()

        product_type = params.get(f"{field}_product_type", cls.PRODUCT_TYPE_DEFAULT)

        if ids := params.get(f"{field}_form_route_ids"):
            form_route_ids = tuple(ids.split(","))
        else:
            form_route_ids = ()

        if ids := params.get(f"{field}_ingredient_ids"):
            ingredient_ids = tuple(ids.split(","))
        else:
            ingredient_ids = ()

        return cls.build(
            raw_terms=raw_terms,
            product_type=product_type,
            form_route_ids=form_route_ids,
            ingredient_ids=ingredient_ids,
        )

    @classmethod
    def from_dict(cls, query_dict):
        bnf_codes_dict = query_dict.get("bnf_codes", {"included": [], "excluded": []})
        included_terms = tuple([Term(rt, False) for rt in bnf_codes_dict["included"]])
        terms = included_terms

        if "excluded" in bnf_codes_dict:
            excluded_terms = tuple(
                [Term(rt, True) for rt in bnf_codes_dict["excluded"]]
            )
            terms += excluded_terms

        product_type = query_dict.get("product_type", cls.PRODUCT_TYPE_DEFAULT)

        form_route_ids = _get_form_route_ids_for_forms_and_routes(
            query_dict.get("form_routes", []),
            query_dict.get("forms", []),
            query_dict.get("routes", []),
        )

        ingredient_ids = tuple(str(i) for i in query_dict.get("ingredient_ids", []))

        return cls(
            terms,
            ProductType(product_type),
            form_route_ids=form_route_ids,
            ingredient_ids=ingredient_ids,
        )

    def to_dict(self):
        included_codes = [term.code for term in self.terms if not term.negated]
        excluded_codes = [term.code for term in self.terms if term.negated]
        bnf_query_dict = {
            "bnf_codes": {"included": included_codes},
        }
        if excluded_codes:
            bnf_query_dict["bnf_codes"]["excluded"] = excluded_codes
        if not self.product_type == ProductType.ALL:
            bnf_query_dict["product_type"] = self.product_type.value
        if self.form_route_ids:
            bnf_query_dict["form_routes"] = [
                str(form_route.descr)
                for form_route in OntFormRoute.objects.filter(
                    cd__in=self.form_route_ids
                )
            ]
        if self.ingredient_ids:
            bnf_query_dict["ingredient_ids"] = list(self.ingredient_ids)

        return bnf_query_dict

    def to_sql(self):
        """Return SQL that returns items prescribed for codes matching query.

        The query returns one row for each practice for each month with data.
        """

        codes = self.get_matching_presentation_codes()

        if codes:
            return f"""
            SELECT practice_id, date_id, items AS value
            FROM prescribing
            WHERE bnf_code IN ({", ".join(f"'{c}'" for c in codes)})
            """
        else:
            return """
            SELECT practice_id, date_id, items AS value
            FROM prescribing
            WHERE false
            """

    def get_matching_presentation_codes(self):
        """Return list of BNF codes for presentations matching the query.

        Returned codes are strings, not BNFCode instances.
        """

        includes = [t.build_q() for t in self.terms if not t.negated]
        excludes = [t.build_q() for t in self.terms if t.negated]

        codes = (
            BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
            .filter(reduce(Q.__or__, includes, Q()))
            .exclude(reduce(Q.__or__, excludes, Q()))
        )

        if self.form_route_ids:
            codes = codes.filter(
                code__in=_get_bnf_codes_for_form_route_ids(self.form_route_ids)
            )

        if self.ingredient_ids:
            codes = codes.filter(
                code__in=_get_bnf_codes_for_ingredient_ids(self.ingredient_ids)
            )

        codes = list(codes.order_by("code").values_list("code", flat=True))

        if self.product_type == ProductType.ALL:
            return codes
        elif self.product_type == ProductType.GENERIC:
            return [c for c in codes if c[9:11] == "AA"]
        elif self.product_type == ProductType.BRANDED:
            return [c for c in codes if c[9:11] != "AA"]
        else:
            assert False, self.product_type

    def describe(self):
        return {
            "product_type": self.product_type,
            "includes": [
                t.describe(self.product_type) for t in self.terms if not t.negated
            ],
            "excludes": [
                t.describe(self.product_type) for t in self.terms if t.negated
            ],
            "form_routes": [
                OntFormRoute.objects.get(cd=fr).descr for fr in self.form_route_ids
            ],
            "ingredient_ids": [
                {
                    "code": ingredient_id,
                    "description": Ing.objects.get(isid=ingredient_id).nm,
                }
                for ingredient_id in self.ingredient_ids
            ],
        }

    def to_params(self, field):
        """Serialize to URL query parameters for a field."""

        params = {
            f"{field}_codes": self.to_codes(),
            f"{field}_product_type": self.product_type.value,
        }
        if self.form_route_ids:
            params[f"{field}_form_route_ids"] = ",".join(self.form_route_ids)
        if self.ingredient_ids:
            params[f"{field}_ingredient_ids"] = ",".join(self.ingredient_ids)

        return params

    def to_codes(self):
        return ",".join(t.to_param_value() for t in self.terms)


@dataclass(frozen=True)
class Term:
    """Represents a term in a query.

    This class will be removed in a subsequent commit.
    """

    code: str
    negated: bool

    @classmethod
    def from_param_value(cls, raw_term):
        if raw_term[0] == "-":
            negated = True
            code = raw_term[1:]
        else:
            negated = False
            code = raw_term
        return cls(code, negated)

    def to_param_value(self):
        if self.negated:
            return "-" + self.code
        else:
            return self.code

    def build_q(self):
        """Return Q object for finding all presentations that match the given code.

        If the code contains an underscore, then it is a "strength and formulation" code,
        consisting of a BNF chemical substance code (nine characters) and a strength and
        formulation part (two characters), separated by an underscore.

        For instance, a query for 040702040_AM returns all presentations belonging to the
        chemical substance 040702040 (Tramadol hydrochloride) that have the same strength
        and formulation as the generic presentation 040702040AAAMAM (Tramadol 300mg
        modified-release tablets).

        If the code does not contain an underscore, then it is a "prefix" code, and matches
        all presentations beginning with that prefix.
        """

        if "_" in self.code:
            prefix, suffix = self.code.split("_")
            assert len(prefix) == 9  # chemical substance code
            assert len(suffix) == 2  # strength and formulation part
            return Q(code__startswith=prefix, code__endswith=suffix)
        else:
            return Q(code__startswith=self.code)

    def describe(self, product_type):
        """Return dict with keys `code` and `description` for describing a search to
        users."""

        if "_" in self.code:
            prefix, suffix = self.code.split("_")
            assert len(prefix) == 9  # chemical substance code
            assert len(suffix) == 2  # strength and formulation part
            generic_code_obj = BNFCode.objects.get(code=f"{prefix}AA{suffix}{suffix}")
            if product_type == ProductType.ALL:
                description = f"{generic_code_obj.name} (branded and generic)"
            else:
                description = generic_code_obj.name
            return {"code": self.code, "description": description}
        else:
            description = BNFCode.objects.get(code=self.code).name
            return {"code": self.code, "description": description}
