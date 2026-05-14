from django.db import models


class NCSOConcessions(models.Model):
    """Model for the price concessions for a drug."""

    date = models.DateField(db_index=True)
    vmpp = models.IntegerField()
    price_pence = models.IntegerField()

    class Meta:
        unique_together = ("date", "vmpp")
