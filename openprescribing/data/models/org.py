from django.db import connections, models


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
        by_id = {org.id: (org, []) for org in self}
        descendants = get_descendents_of_type(
            org_type=Org.OrgType.PRACTICE,
            org_ids=by_id.keys(),
        )
        for org_id, practice_id in descendants:
            by_id[org_id][1].append(practice_id)
        return tuple(
            (org, frozenset(practice_ids)) for org, practice_ids in by_id.values()
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


def get_descendents_of_type(org_type, org_ids):
    """
    Given a list of Org IDs find all descendant Orgs of the requested type

    Return the result as a list of pairs of IDs:

        parent_org_1, descendant_org_1
        parent_org_1, descendant_org_2
        parent_org_2, descendant_org_3
        ...

    """
    if not org_ids:
        return []

    org_id_placeholders = ", ".join(["(%s)"] * len(org_ids))
    orgs_sql = f"""\
    WITH RECURSIVE

        root_org(id) AS (
            VALUES {org_id_placeholders}
        ),

        descendant AS (
            SELECT
                root_org.id AS root_id,
                root_org.id AS child_id
            FROM
                root_org

            UNION ALL

            SELECT
                descendant.root_id,
                org_relation.child_id
            FROM
                org_relation
            JOIN
                descendant ON descendant.child_id = org_relation.parent_id
        )

    SELECT DISTINCT
      descendant.root_id,
      org.id
    FROM descendant
    JOIN org ON org.id = descendant.child_id
    WHERE org.org_type = %s
    """
    with connections["data"].cursor() as cursor:
        return cursor.execute(orgs_sql, [*org_ids, org_type]).fetchall()
