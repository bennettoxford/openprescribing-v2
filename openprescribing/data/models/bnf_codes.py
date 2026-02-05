import collections
import re
from functools import cached_property

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

    @cached_property
    def parts(self):
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
        Parts = collections.namedtuple("Parts", match.groupdict().keys())
        return Parts(**match.groupdict())

    def is_generic(self):
        assert self.level in [BNFCode.Level.PRODUCT, BNFCode.Level.PRESENTATION]
        return self.parts.product == "AA"

    def is_ancestor_of(self, other):
        return other.code != self.code and other.code.startswith(self.code)

    def is_generic_equivalent_of(self, other):
        assert self.level == BNFCode.Level.PRESENTATION
        assert other.level == BNFCode.Level.PRESENTATION
        assert self.is_generic()
        return (
            self.parts.chapter == other.parts.chapter
            and self.parts.section == other.parts.section
            and self.parts.paragraph == other.parts.paragraph
            and self.parts.subparagraph == other.parts.subparagraph
            and self.parts.chemical_substance == other.parts.chemical_substance
            and self.parts.strength_and_formulation == other.parts.generic_equivalent
        )
