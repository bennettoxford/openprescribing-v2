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


def _get_bnf_codes_for_form_routes(form_routes):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            """
            SELECT bnf_code
            FROM medications
            WHERE list_has_any(form_routes, ?)
            """,
            [list(form_routes)],
        )
        return [x[0] for x in results.fetchall()]


def _expand_forms_and_routes(forms, routes):
    """Return the form/route descriptions matching all of the given forms and routes.

    A `form` matches form/routes whose description starts with `{form}.` and a `route`
    matches form/routes whose description ends with `.{route}`; when both forms and
    routes are given a description must match all of them. Returns an empty list when no
    forms or routes are given, or when nothing matches.
    """

    if not forms and not routes:
        return []

    conditions = [Q(descr__endswith=f".{route}") for route in routes]
    conditions += [Q(descr__startswith=f"{form}.") for form in forms]
    query = reduce(and_, conditions)

    return [form_route.descr for form_route in OntFormRoute.objects.filter(query)]


def _get_bnf_codes_for_ingredient_ids(ingredient_ids):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            f"""
            SELECT bnf_code
            FROM medications
            WHERE list_has_any(ingredient_ids, [{", ".join(str(i) for i in ingredient_ids)}])
            """
        )
        return [x[0] for x in results.fetchall()]


def _get_bnf_codes_for_vtm_ids(vtm_ids):
    with rxdb.get_cursor() as cursor:
        results = cursor.execute(
            f"""
            SELECT bnf_code
            FROM medications
            WHERE vtm_id IN ({", ".join(str(i) for i in vtm_ids)})
            """
        )
        return [x[0] for x in results.fetchall()]


@dataclass(frozen=True)
class BNFQuery:
    """Represents a query returning codes for BNF presentations."""

    bnf_codes: tuple[str] = ()
    bnf_codes_excluded: tuple[str] = ()
    product_type: ProductType = ProductType.ALL
    form_routes: tuple[str] = ()
    form_routes_excluded: tuple[str] = ()
    forms: tuple[str] = ()
    forms_excluded: tuple[str] = ()
    routes: tuple[str] = ()
    routes_excluded: tuple[str] = ()
    ingredient_ids: tuple[int] = ()
    ingredient_ids_excluded: tuple[int] = ()
    vtm_ids: tuple[int] = ()
    vtm_ids_excluded: tuple[int] = ()

    PRODUCT_TYPE_DEFAULT = "all"

    def __post_init__(self):
        """Ensure that all sequence attributes are tuples.

        object.__setattr__ is required because the dataclass is frozen.
        """

        object.__setattr__(self, "bnf_codes", tuple(self.bnf_codes))
        object.__setattr__(self, "bnf_codes_excluded", tuple(self.bnf_codes_excluded))
        object.__setattr__(self, "form_routes", tuple(self.form_routes))
        object.__setattr__(
            self, "form_routes_excluded", tuple(self.form_routes_excluded)
        )
        object.__setattr__(self, "forms", tuple(self.forms))
        object.__setattr__(self, "forms_excluded", tuple(self.forms_excluded))
        object.__setattr__(self, "routes", tuple(self.routes))
        object.__setattr__(self, "routes_excluded", tuple(self.routes_excluded))
        object.__setattr__(
            self, "ingredient_ids", tuple(int(i) for i in self.ingredient_ids)
        )
        object.__setattr__(
            self,
            "ingredient_ids_excluded",
            tuple(int(i) for i in self.ingredient_ids_excluded),
        )
        object.__setattr__(self, "vtm_ids", tuple(int(i) for i in self.vtm_ids))
        object.__setattr__(
            self, "vtm_ids_excluded", tuple(int(i) for i in self.vtm_ids_excluded)
        )

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
        form_routes = _get_tuple_param(params, f"{field}_form_routes")
        form_routes_excluded = _get_tuple_param(params, f"{field}_form_routes_excluded")
        forms = _get_tuple_param(params, f"{field}_forms")
        forms_excluded = _get_tuple_param(params, f"{field}_forms_excluded")
        routes = _get_tuple_param(params, f"{field}_routes")
        routes_excluded = _get_tuple_param(params, f"{field}_routes_excluded")
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
            form_routes=form_routes,
            form_routes_excluded=form_routes_excluded,
            forms=forms,
            forms_excluded=forms_excluded,
            routes=routes,
            routes_excluded=routes_excluded,
            ingredient_ids=ingredient_ids,
            ingredient_ids_excluded=ingredient_ids_excluded,
            vtm_ids=vtm_ids,
            vtm_ids_excluded=vtm_ids_excluded,
        )

    @classmethod
    def from_dict(cls, query_dict):
        bnf_codes_dict = query_dict.get("bnf_codes", {"included": [], "excluded": []})
        product_type = query_dict.get("product_type", cls.PRODUCT_TYPE_DEFAULT)

        form_routes = tuple(query_dict.get("form_routes", []))
        form_routes_excluded = tuple(query_dict.get("form_routes_excluded", []))
        forms = tuple(query_dict.get("forms", []))
        forms_excluded = tuple(query_dict.get("forms_excluded", []))
        routes = tuple(query_dict.get("routes", []))
        routes_excluded = tuple(query_dict.get("routes_excluded", []))

        ingredient_ids = tuple(query_dict.get("ingredient_ids", []))
        ingredient_ids_excluded = tuple(query_dict.get("ingredient_ids_excluded", []))

        vtm_ids = tuple(query_dict.get("vtm_ids", []))
        vtm_ids_excluded = tuple(query_dict.get("vtm_ids_excluded", []))

        return cls(
            tuple(bnf_codes_dict["included"]),
            tuple(bnf_codes_dict.get("excluded", [])),
            ProductType(product_type),
            form_routes=form_routes,
            form_routes_excluded=form_routes_excluded,
            forms=forms,
            forms_excluded=forms_excluded,
            routes=routes,
            routes_excluded=routes_excluded,
            ingredient_ids=ingredient_ids,
            ingredient_ids_excluded=ingredient_ids_excluded,
            vtm_ids=vtm_ids,
            vtm_ids_excluded=vtm_ids_excluded,
        )

    def to_dict(self):
        bnf_query_dict = {
            "bnf_codes": {"included": list(self.bnf_codes)},
        }
        if self.bnf_codes_excluded:
            bnf_query_dict["bnf_codes"]["excluded"] = list(self.bnf_codes_excluded)
        if not self.product_type == ProductType.ALL:
            bnf_query_dict["product_type"] = self.product_type.value
        if self.form_routes:
            bnf_query_dict["form_routes"] = list(self.form_routes)
        if self.form_routes_excluded:
            bnf_query_dict["form_routes_excluded"] = list(self.form_routes_excluded)
        if self.forms:
            bnf_query_dict["forms"] = list(self.forms)
        if self.forms_excluded:
            bnf_query_dict["forms_excluded"] = list(self.forms_excluded)
        if self.routes:
            bnf_query_dict["routes"] = list(self.routes)
        if self.routes_excluded:
            bnf_query_dict["routes_excluded"] = list(self.routes_excluded)
        if self.ingredient_ids:
            bnf_query_dict["ingredient_ids"] = list(self.ingredient_ids)
        if self.ingredient_ids_excluded:
            bnf_query_dict["ingredient_ids_excluded"] = list(
                self.ingredient_ids_excluded
            )
        if self.vtm_ids:
            bnf_query_dict["vtm_ids"] = list(self.vtm_ids)
        if self.vtm_ids_excluded:
            bnf_query_dict["vtm_ids_excluded"] = list(self.vtm_ids_excluded)

        return bnf_query_dict

    def to_sql(self):
        """Return SQL that returns items prescribed for codes matching query.

        The query returns one row for each practice for each month with data.
        """

        codes = self.get_matching_presentation_codes()

        if codes:
            return f"""
            SELECT presentation_id, practice_id, date_id, items AS value
            FROM prescribing
            WHERE bnf_code IN ({", ".join(f"'{c}'" for c in codes)})
            """
        else:
            return """
            SELECT presentation_id, practice_id, date_id, items AS value
            FROM prescribing
            WHERE false
            """

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

        form_routes = list(self.form_routes) + _expand_forms_and_routes(
            self.forms, self.routes
        )
        form_routes_excluded = list(
            self.form_routes_excluded
        ) + _expand_forms_and_routes(self.forms_excluded, self.routes_excluded)
        if form_routes:
            codes = codes.filter(code__in=_get_bnf_codes_for_form_routes(form_routes))
        if form_routes_excluded:
            codes = codes.exclude(
                code__in=_get_bnf_codes_for_form_routes(form_routes_excluded)
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
            "form_routes": list(self.form_routes),
            "form_routes_excluded": list(self.form_routes_excluded),
            "forms": list(self.forms),
            "forms_excluded": list(self.forms_excluded),
            "routes": list(self.routes),
            "routes_excluded": list(self.routes_excluded),
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
        if self.form_routes:
            params[f"{field}_form_routes"] = ",".join(self.form_routes)
        if self.form_routes_excluded:
            params[f"{field}_form_routes_excluded"] = ",".join(
                self.form_routes_excluded
            )
        if self.forms:
            params[f"{field}_forms"] = ",".join(self.forms)
        if self.forms_excluded:
            params[f"{field}_forms_excluded"] = ",".join(self.forms_excluded)
        if self.routes:
            params[f"{field}_routes"] = ",".join(self.routes)
        if self.routes_excluded:
            params[f"{field}_routes_excluded"] = ",".join(self.routes_excluded)
        if self.ingredient_ids:
            params[f"{field}_ingredient_ids"] = ",".join(
                str(i) for i in self.ingredient_ids
            )
        if self.ingredient_ids_excluded:
            params[f"{field}_ingredient_ids_excluded"] = ",".join(
                str(i) for i in self.ingredient_ids_excluded
            )
        if self.vtm_ids:
            params[f"{field}_vtm_ids"] = ",".join(str(i) for i in self.vtm_ids)
        if self.vtm_ids_excluded:
            params[f"{field}_vtm_ids_excluded"] = ",".join(
                str(i) for i in self.vtm_ids_excluded
            )

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
        prefix, suffix = destructure_strength_and_formulation_code(code)
        return Q(code__startswith=prefix, code__endswith=suffix)
    else:
        return Q(code__startswith=code)


def description_for_bnf_code(code, product_type):
    """Return a human-readable description for a BNF code."""

    if "_" in code:
        prefix, suffix = destructure_strength_and_formulation_code(code)
        generic_code_obj = BNFCode.objects.get(code=f"{prefix}AA{suffix}{suffix}")
        if product_type == ProductType.ALL:
            return f"{generic_code_obj.name} (branded and generic)"
        else:
            return generic_code_obj.name
    else:
        return BNFCode.objects.get(code=code).name


def destructure_strength_and_formulation_code(code):
    assert "_" in code
    prefix, suffix = code.split("_", 1)
    if len(prefix) == 9 and len(suffix) == 2:
        return prefix, suffix
    raise ValueError(f"Invalid strength and formulation code: {code}")


def _get_tuple_param(params, key):
    if value := params.get(key):
        return tuple(value.split(","))
    return ()
