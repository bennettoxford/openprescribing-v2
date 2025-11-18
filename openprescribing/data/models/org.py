from django.db import models


class Org(models.Model):
    class Meta:
        db_table = "org"

    class OrgType(models.TextChoices):
        NATION = ("nat", "Nation")
        REGION = ("reg", "Region")
        ICB = ("icb", "ICB")
        SICBL = ("sic", "SICBL")
        PCN = ("pcn", "PCN")
        PRACTICE = ("pra", "Practice")
        OTHER = ("oth", "Other")

    id = models.TextField(primary_key=True)
    org_type = models.TextField(choices=OrgType, db_index=True)
    name = models.TextField()
    inactive = models.BooleanField(default=False)

    parents = models.ManyToManyField(
        "self",
        related_name="children",
        through="OrgRelation",
        through_fields=("child", "parent"),
        symmetrical=False,
    )

    def __repr__(self):
        return f"Org({self.id!r}, {self.OrgType(self.org_type)!r}, {self.name!r})"


class OrgRelation(models.Model):
    class Meta:
        db_table = "org_relation"

    child = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="+",
    )
    parent = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="+",
    )
