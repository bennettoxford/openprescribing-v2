from django.db import models


class DmdBnfMap(models.Model):
    """Corresponds to an entry in the BNF SNOMED mapping file from
    https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping.

    As far as we're concerned, "SNOMED code" and "dm+d code" are interchangeable, so we
    just talk about dm+d.
    """

    class Meta:
        db_table = "dmd_bnf_map"

    dmd_id = models.IntegerField()
    bnf_code = models.CharField(max_length=15)
