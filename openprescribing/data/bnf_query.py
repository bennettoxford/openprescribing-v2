from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import reduce

from django.db.models import Q

from .models import BNFCode


@dataclass
class BNFQuery:
    """Represents a query returning codes for BNF presentations."""

    terms: list[Term]
    product_type: ProductType

    @classmethod
    def build(cls, raw_terms, product_type):
        return cls([Term.build(rt) for rt in raw_terms], ProductType(product_type))

    def get_matching_presentation_codes(self):
        """Return list of BNF codes for presentations matching the query.

        Returned codes are strings, not BNFCode instances.
        """

        includes = [t.build_q() for t in self.terms if not t.negated]
        excludes = [t.build_q() for t in self.terms if t.negated]

        codes = list(
            BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
            .filter(reduce(Q.__or__, includes, Q()))  # TODO?
            .exclude(reduce(Q.__or__, excludes, Q()))
            .order_by("code")
            .values_list("code", flat=True)
        )

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


@dataclass
class Term:
    """Represents a term in a query.

    See subclasses for more.
    """

    code: str
    negated: bool

    @staticmethod
    def build(raw_term):
        if raw_term[0] == "-":
            negated = True
            code = raw_term[1:]
        else:
            negated = False
            code = raw_term
        if "_" in code:
            return StrengthAndFormulationTerm(code, negated)
        else:
            return PrefixTerm(code, negated)


@dataclass
class PrefixTerm(Term):
    """Represents a query for all presentations below an object in the BNF hierarchy."""

    def build_q(self):
        return Q(code__startswith=self.code)

    def describe(self, product_type):
        description = BNFCode.objects.get(code=self.code).name
        return {"code": self.code, "description": description}


@dataclass
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
        self.prefix, self.suffix = self.code.split("_")
        assert len(self.prefix) == 9  # chemical substance code
        assert len(self.suffix) == 2  # strength and formulation part

    def build_q(self):
        return Q(code__startswith=self.prefix, code__endswith=self.suffix)

    def describe(self, product_type):
        generic_code_obj = BNFCode.objects.get(
            code=f"{self.prefix}AA{self.suffix}{self.suffix}"
        )
        if product_type == ProductType.ALL:
            description = f"{generic_code_obj.name} (branded and generic)"
        else:
            description = generic_code_obj.name
        return {"code": self.code, "description": description}


class ProductType(StrEnum):
    ALL = "all"
    GENERIC = "generic"
    BRANDED = "branded"
