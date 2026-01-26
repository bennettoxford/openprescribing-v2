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
        boundaries = [0, 2, 4, 6, 7, 9, 11, 13, 15]
        kwargs = {}
        for ix, field in enumerate(Slots.__dataclass_fields__):
            if len(self.code) >= boundaries[ix + 1]:
                kwargs[field] = self.code[boundaries[ix] : boundaries[ix + 1]]
            else:
                kwargs[field] = None
        return Slots(**kwargs)

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
