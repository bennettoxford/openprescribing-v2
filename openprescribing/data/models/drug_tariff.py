from django.db import models


class TariffPrice(models.Model):
    """Model for the price of a drug in the Drug Tariff."""

    date = models.DateField(db_index=True)
    vmpp_id = models.IntegerField()
    # These IDs correspond to the dmd.DtPaymentCategory model.
    # 1: Category A
    # 3: Category C
    # 11: Category M
    # 15: Category H
    drug_tariff_category_id = models.IntegerField()
    price_in_pence = models.IntegerField()

    class Meta:
        unique_together = ("date", "vmpp_id")
