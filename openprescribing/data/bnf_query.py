from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import reduce
from operator import and_

from django.db.models import Q

from openprescribing.data import rxdb
from openprescribing.data.models.dmd import VTM, Ing, OntFormRoute

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
    if not form_routes and not forms and not routes:
        return []

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


def _get_bnf_codes_for_vtm_ids(vtm_ids):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            f"""
            SELECT bnf_code
            FROM medications
            WHERE vtm_id IN ({", ".join(vtm_ids)})
            """
        )
        return [x[0] for x in results.fetchall()]


def _build_sql_for_codes(codes):
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


@dataclass(frozen=True)
class BNFQuery:
    """Represents a query returning codes for BNF presentations."""

    bnf_codes: tuple[str] = ()
    bnf_codes_excluded: tuple[str] = ()
    product_type: ProductType = ProductType.ALL
    form_route_ids: tuple[str] = ()
    form_route_ids_excluded: tuple[str] = ()
    ingredient_ids: tuple[str] = ()
    ingredient_ids_excluded: tuple[str] = ()
    vtm_ids: tuple[str] = ()
    vtm_ids_excluded: tuple[str] = ()

    PRODUCT_TYPE_DEFAULT = "all"

    def __post_init__(self):
        """Ensure that all sequence attributes are tuples.

        object.__setattr__ is required because the dataclass is frozen.
        """

        object.__setattr__(self, "bnf_codes", tuple(self.bnf_codes))
        object.__setattr__(self, "bnf_codes_excluded", tuple(self.bnf_codes_excluded))
        object.__setattr__(self, "form_route_ids", tuple(self.form_route_ids))
        object.__setattr__(
            self, "form_route_ids_excluded", tuple(self.form_route_ids_excluded)
        )
        object.__setattr__(self, "ingredient_ids", tuple(self.ingredient_ids))
        object.__setattr__(
            self, "ingredient_ids_excluded", tuple(self.ingredient_ids_excluded)
        )
        object.__setattr__(self, "vtm_ids", tuple(self.vtm_ids))
        object.__setattr__(self, "vtm_ids_excluded", tuple(self.vtm_ids_excluded))

    @staticmethod
    def has_params(field, params):
        """Indicate whether any of given params belong to given field."""

        return any(key.startswith(f"{field}_") for key in params)

    @classmethod
    def from_params(cls, field, params):
        """Build a BNFQuery from URL query parameters for a field."""

        bnf_codes = _get_tuple_param(params, f"{field}_bnf_codes")
        bnf_codes_excluded = _get_tuple_param(params, f"{field}_bnf_codes_excluded")
        product_type = params.get(f"{field}_product_type", cls.PRODUCT_TYPE_DEFAULT)
        form_route_ids = _get_tuple_param(params, f"{field}_form_route_ids")
        form_route_ids_excluded = _get_tuple_param(
            params, f"{field}_form_route_ids_excluded"
        )
        ingredient_ids = _get_tuple_param(params, f"{field}_ingredient_ids")
        ingredient_ids_excluded = _get_tuple_param(
            params, f"{field}_ingredient_ids_excluded"
        )
        vtm_ids = _get_tuple_param(params, f"{field}_vtm_ids")
        vtm_ids_excluded = _get_tuple_param(params, f"{field}_vtm_ids_excluded")

        return cls(
            bnf_codes=bnf_codes,
            bnf_codes_excluded=bnf_codes_excluded,
            product_type=ProductType(product_type),
            form_route_ids=form_route_ids,
            form_route_ids_excluded=form_route_ids_excluded,
            ingredient_ids=ingredient_ids,
            ingredient_ids_excluded=ingredient_ids_excluded,
            vtm_ids=vtm_ids,
            vtm_ids_excluded=vtm_ids_excluded,
        )

    @classmethod
    def from_dict(cls, query_dict):
        bnf_codes_dict = query_dict.get("bnf_codes", {"included": [], "excluded": []})
        product_type = query_dict.get("product_type", cls.PRODUCT_TYPE_DEFAULT)

        form_route_ids = _get_form_route_ids_for_forms_and_routes(
            query_dict.get("form_routes", []),
            query_dict.get("forms", []),
            query_dict.get("routes", []),
        )

        ingredient_ids = tuple(str(i) for i in query_dict.get("ingredient_ids", []))

        return cls(
            tuple(bnf_codes_dict["included"]),
            tuple(bnf_codes_dict.get("excluded", [])),
            ProductType(product_type),
            form_route_ids=form_route_ids,
            ingredient_ids=ingredient_ids,
        )

    def to_dict(self):
        bnf_query_dict = {
            "bnf_codes": {"included": list(self.bnf_codes)},
        }
        if self.bnf_codes_excluded:
            bnf_query_dict["bnf_codes"]["excluded"] = list(self.bnf_codes_excluded)
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

        return _build_sql_for_codes(codes)

    def get_matching_presentation_codes(self):
        """Return list of BNF codes for presentations matching the query.

        Returned codes are strings, not BNFCode instances.
        """

        includes = [build_q_for_bnf_code(code) for code in self.bnf_codes]
        excludes = [build_q_for_bnf_code(code) for code in self.bnf_codes_excluded]

        codes = (
            BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
            .filter(reduce(Q.__or__, includes, Q()))
            .exclude(reduce(Q.__or__, excludes, Q()))
        )

        if self.form_route_ids:
            codes = codes.filter(
                code__in=_get_bnf_codes_for_form_route_ids(self.form_route_ids)
            )
        if self.form_route_ids_excluded:
            codes = codes.exclude(
                code__in=_get_bnf_codes_for_form_route_ids(self.form_route_ids_excluded)
            )

        if self.ingredient_ids:
            codes = codes.filter(
                code__in=_get_bnf_codes_for_ingredient_ids(self.ingredient_ids)
            )
        if self.ingredient_ids_excluded:
            codes = codes.exclude(
                code__in=_get_bnf_codes_for_ingredient_ids(self.ingredient_ids_excluded)
            )
        if self.vtm_ids:
            codes = codes.filter(code__in=_get_bnf_codes_for_vtm_ids(self.vtm_ids))
        if self.vtm_ids_excluded:
            codes = codes.exclude(
                code__in=_get_bnf_codes_for_vtm_ids(self.vtm_ids_excluded)
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
            "bnf_codes": [
                description_for_bnf_code(code, self.product_type)
                for code in self.bnf_codes
            ],
            "bnf_codes_excluded": [
                description_for_bnf_code(code, self.product_type)
                for code in self.bnf_codes_excluded
            ],
            "form_routes": [
                OntFormRoute.objects.get(cd=fr).descr for fr in self.form_route_ids
            ],
            "form_routes_excluded": [
                OntFormRoute.objects.get(cd=fr).descr
                for fr in self.form_route_ids_excluded
            ],
            "ingredients": [
                Ing.objects.get(isid=ingredient_id).nm
                for ingredient_id in self.ingredient_ids
            ],
            "ingredients_excluded": [
                Ing.objects.get(isid=ingredient_id).nm
                for ingredient_id in self.ingredient_ids_excluded
            ],
            "vtms": [VTM.objects.get(vtmid=vtm_id).nm for vtm_id in self.vtm_ids],
            "vtms_excluded": [
                VTM.objects.get(vtmid=vtm_id).nm for vtm_id in self.vtm_ids_excluded
            ],
        }

    def to_params(self, field):
        """Serialize to URL query parameters for a field."""

        params = {f"{field}_product_type": self.product_type.value}
        if self.bnf_codes:
            params[f"{field}_bnf_codes"] = ",".join(self.bnf_codes)
        if self.bnf_codes_excluded:
            params[f"{field}_bnf_codes_excluded"] = ",".join(self.bnf_codes_excluded)
        if self.form_route_ids:
            params[f"{field}_form_route_ids"] = ",".join(self.form_route_ids)
        if self.form_route_ids_excluded:
            params[f"{field}_form_route_ids_excluded"] = ",".join(
                self.form_route_ids_excluded
            )
        if self.ingredient_ids:
            params[f"{field}_ingredient_ids"] = ",".join(self.ingredient_ids)
        if self.ingredient_ids_excluded:
            params[f"{field}_ingredient_ids_excluded"] = ",".join(
                self.ingredient_ids_excluded
            )
        if self.vtm_ids:
            params[f"{field}_vtm_ids"] = ",".join(self.vtm_ids)
        if self.vtm_ids_excluded:
            params[f"{field}_vtm_ids_excluded"] = ",".join(self.vtm_ids_excluded)

        return params


def build_q_for_bnf_code(code):
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

    if "_" in code:
        prefix, suffix = code.split("_")
        assert len(prefix) == 9  # chemical substance code
        assert len(suffix) == 2  # strength and formulation part
        return Q(code__startswith=prefix, code__endswith=suffix)
    else:
        return Q(code__startswith=code)


@dataclass(frozen=True)
class MultiBNFQuery:
    # This is a tuple rather than a list so that it is hashable, so that we
    # can use functools.lru_cache for get_practice_date_matrix()
    queries: tuple[BNFQuery]

    @classmethod
    def from_list(cls, queries):
        bnf_queries = tuple([q for q in queries if isinstance(q, BNFQuery)])
        return cls(queries=bnf_queries)

    def to_sql(self):
        codes = self.get_matching_presentation_codes()
        return _build_sql_for_codes(codes)

    def get_matching_presentation_codes(self):
        matching_codes = [
            query.get_matching_presentation_codes() for query in self.queries
        ]

        unique_matching_codes = sorted(
            list({code for codes in matching_codes for code in codes})
        )

        return unique_matching_codes


def description_for_bnf_code(code, product_type):
    """Return a human-readable description for a BNF code."""

    if "_" in code:
        prefix, suffix = code.split("_")
        assert len(prefix) == 9  # chemical substance code
        assert len(suffix) == 2  # strength and formulation part
        generic_code_obj = BNFCode.objects.get(code=f"{prefix}AA{suffix}{suffix}")
        if product_type == ProductType.ALL:
            return f"{generic_code_obj.name} (branded and generic)"
        else:
            return generic_code_obj.name
    else:
        return BNFCode.objects.get(code=code).name


def _get_tuple_param(params, key):
    if value := params.get(key):
        return tuple(value.split(","))
    return ()
