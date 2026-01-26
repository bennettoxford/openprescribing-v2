import re
from dataclasses import dataclass

from django.db import models


class BNFCode(models.Model):
    class Meta:
        db_table = "bnf_code"

    class Level(models.IntegerChoices):
        CHAPTER = 1
        SECTION = 2
        PARAGRAPH = 3
        SUBPARAGRAPH = 4
        CHEMICAL_SUBSTANCE = 5
        PRODUCT = 6
        PRESENTATION = 7

    code = models.TextField(primary_key=True)
    level = models.IntegerField(choices=Level)
    name = models.TextField()

    @property
    def slots(self):
        pattern = r"""
            \A
            (?P<chapter>.{2})
            (?P<section>.{2})?
            (?P<paragraph>.{2})?
            (?P<subparagraph>.{1})?
            (?P<chemical_substance>.{2})?
            (?P<product>.{2})?
            (?P<strength_and_formulation>.{2})?
            (?P<generic_equivalent>.{2})?
            \Z
        """
        match = re.match(pattern, self.code, re.VERBOSE)
        return Slots(**match.groupdict())

    def is_generic(self):
        assert self.level in [BNFCode.Level.PRODUCT, BNFCode.Level.PRESENTATION]
        return self.slots.product == "AA"

    def is_ancestor_of(self, other):
        return other.code != self.code and other.code.startswith(self.code)

    def is_generic_equivalent_of(self, other):
        assert self.level == BNFCode.Level.PRESENTATION
        assert other.level == BNFCode.Level.PRESENTATION
        assert self.is_generic()
        return (
            self.slots.chapter == other.slots.chapter
            and self.slots.section == other.slots.section
            and self.slots.paragraph == other.slots.paragraph
            and self.slots.subparagraph == other.slots.subparagraph
            and self.slots.chemical_substance == other.slots.chemical_substance
            and self.slots.strength_and_formulation == other.slots.generic_equivalent
        )


@dataclass
class Slots:
    chapter: str | None
    section: str | None
    paragraph: str | None
    subparagraph: str | None
    chemical_substance: str | None
    product: str | None
    strength_and_formulation: str | None
    generic_equivalent: str | None
