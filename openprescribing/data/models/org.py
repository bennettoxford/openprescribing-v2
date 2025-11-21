from django.db import models


class OrgQuerySet(models.QuerySet):
    def with_practice_ids(self):
        """
        Return each Org in the QuerySet paired with the IDs of all the practices which
        belong to it:

            Org("parent_1", ...), {"practice_1", "practice_2", "practice_3"}
            Org("parent_2", ...), {"practice_4", "practice_5"}
            ...

        This is the structure required by `LabelledMatrix.group_rows()` so this can be
        used to group a practice-date matrix into higher level organisations.
        """
        orgs_by_id = {
            org.id: (
                org,
                # We consider practices as "belonging" to themselves as this makes the
                # behaviour we want elsewhere drop out neatly
                [org.id] if org.org_type == Org.OrgType.PRACTICE else [],
            )
            for org in self
        }
        relations = OrgRelation.objects.filter(
            parent__in=orgs_by_id.keys(), child__org_type=Org.OrgType.PRACTICE
        )
        for org_id, practice_id in relations.values_list("parent_id", "child_id"):
            orgs_by_id[org_id][1].append(practice_id)
        return tuple(
            (org, frozenset(practice_ids)) for org, practice_ids in orgs_by_id.values()
        )


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

    objects = OrgQuerySet.as_manager()

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
