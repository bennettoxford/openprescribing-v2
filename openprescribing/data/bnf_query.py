from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import reduce

from django.db.models import Q

from openprescribing.data import rxdb

from .models import BNFCode


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


@dataclass(frozen=True)
class BNFQuery:
    """Represents a query returning codes for BNF presentations."""

    terms: tuple[Term]
    product_type: ProductType
    form_route_ids: tuple[str, ...] = ()

    PRODUCT_TYPE_DEFAULT = "all"

    @classmethod
    def build(cls, raw_terms, product_type, form_route_ids=()):
        return cls(
            tuple([Term.from_param_value(rt) for rt in raw_terms]),
            ProductType(product_type),
            tuple(form_route_ids),
        )

    @classmethod
    def from_params(cls, field, params):
        """Build a BNFQuery from URL query parameters for a field."""

        raw_terms = tuple(params[f"{field}_codes"].split(","))
        product_type = params.get(f"{field}_product_type", cls.PRODUCT_TYPE_DEFAULT)

        if ids := params.get(f"{field}_form_route_ids"):
            form_route_ids = tuple(ids.split(","))
        else:
            form_route_ids = ()

        return cls.build(
            raw_terms=raw_terms,
            product_type=product_type,
            form_route_ids=form_route_ids,
        )

    @classmethod
    def from_dict(cls, query_dict):
        bnf_codes_dict = query_dict["bnf_codes"]
        included_terms = tuple(
            [Term.create(rt, False) for rt in bnf_codes_dict["included"]]
        )
        terms = included_terms

        if "excluded" in bnf_codes_dict:
            excluded_terms = tuple(
                [Term.create(rt, True) for rt in bnf_codes_dict["excluded"]]
            )
            terms += excluded_terms

        product_type = query_dict.get("product_type", cls.PRODUCT_TYPE_DEFAULT)

        return cls(
            terms,
            ProductType(product_type),
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

        return bnf_query_dict

    def to_sql(self):
        """Return SQL that returns items prescribed for codes matching query.

        The query returns one row for each practice for each month with data.
        """

        codes = self.get_matching_presentation_codes()

        return f"""
        SELECT practice_id, date_id, items AS value
        FROM prescribing
        WHERE bnf_code IN ({", ".join(f"'{c}'" for c in codes)})
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
        }

    def to_params(self, field):
        """Serialize to URL query parameters for a field."""

        params = {
            f"{field}_codes": self.to_codes(),
            f"{field}_product_type": self.product_type.value,
        }
        if self.form_route_ids:
            params[f"{field}_form_route_ids"] = ",".join(self.form_route_ids)

        return params

    def to_codes(self):
        return ",".join(t.to_param_value() for t in self.terms)


@dataclass(frozen=True)
class Term:
    """Represents a term in a query.

    See subclasses for more.
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
        return cls.create(code, negated)

    @staticmethod
    def create(code, negated):
        if "_" in code:
            return StrengthAndFormulationTerm(code, negated)
        else:
            return PrefixTerm(code, negated)

    def to_param_value(self):
        if self.negated:
            return "-" + self.code
        else:
            return self.code


@dataclass(frozen=True)
class PrefixTerm(Term):
    """Represents a query for all presentations below an object in the BNF hierarchy."""

    def build_q(self):
        return Q(code__startswith=self.code)

    def describe(self, product_type):
        description = BNFCode.objects.get(code=self.code).name
        return {"code": self.code, "description": description}


@dataclass(frozen=True)
class StrengthAndFormulationTerm(Term):
    """Represents a query for all presentations with a given strength and formulation.

    A strength and formulation code consists of a BNF chemical substance code (nine
    characters) and a strength and formulation part (two characters), separated by an
    underscore.

    For instance, a query for 040702040_AM returns all presentations belonging to the
    chemical substance 040702040 (Tramadol hydrochloride) that have the same strength
    and formulation as the generic presentation 040702040AAAMAM (Tramadol 300mg
    modified-release tablets).
    """

    def __post_init__(self):
        prefix, suffix = self.code.split("_")
        assert len(prefix) == 9  # chemical substance code
        assert len(suffix) == 2  # strength and formulation part

    def build_q(self):
        prefix, suffix = self.code.split("_")
        return Q(code__startswith=prefix, code__endswith=suffix)

    def describe(self, product_type):
        prefix, suffix = self.code.split("_")
        generic_code_obj = BNFCode.objects.get(code=f"{prefix}AA{suffix}{suffix}")
        if product_type == ProductType.ALL:
            description = f"{generic_code_obj.name} (branded and generic)"
        else:
            description = generic_code_obj.name
        return {"code": self.code, "description": description}


class ProductType(StrEnum):
    ALL = "all"
    GENERIC = "generic"
    BRANDED = "branded"
