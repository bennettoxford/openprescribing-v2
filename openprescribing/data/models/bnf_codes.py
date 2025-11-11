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
