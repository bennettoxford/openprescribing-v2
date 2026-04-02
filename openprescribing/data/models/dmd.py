# This module defines ORM classes for dm+d data.
#
# The main dm+d classes are:
#
# * Virtual Therapeutic Moeties (VTMs)
# * Virtual Medicinal Products (VMPs)
# * Actual Medicinal Products (AMPs)
# * Virtual Medicinal Product Packs (VMPPs)
# * Actual Medicinal Product Packs (AMPPs)
#
# For more about the dm+d data model, see:
#
#   https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/nhs-dictionary-medicines-and-devices-dmd
#
# The order of the classes in this file and the order of fields within classes match the
# order of the data types defined in the XML data files.
#
# In most cases, the names of classes, tables, and fields match the names from the raw
# XML data.  Exceptions are documented in ingestors.dmd.build_instance.

from django.db import models


class VTM(models.Model):
    class Meta:
        db_table = "vtm"

    vtmid = models.BigIntegerField(primary_key=True)
    invalid = models.BooleanField()
    nm = models.CharField(max_length=255)
    abbrevnm = models.CharField(max_length=60, null=True)
    vtmidprev = models.BigIntegerField(null=True)
    vtmiddt = models.DateField(null=True)


class VMP(models.Model):
    class Meta:
        db_table = "vmp"

    vpid = models.BigIntegerField(primary_key=True)
    vpiddt = models.DateField(null=True)
    vpidprev = models.BigIntegerField(null=True)
    vtm = models.ForeignKey(
        db_column="vtmid",
        to=VTM,
        on_delete=models.CASCADE,
        null=True,
    )
    invalid = models.BooleanField()
    nm = models.CharField(max_length=255)
    abbrevnm = models.CharField(max_length=60, null=True)
    basis = models.ForeignKey(
        db_column="basiscd",
        to="BasisOfName",
        on_delete=models.CASCADE,
    )
    nmdt = models.DateField(null=True)
    nmprev = models.CharField(max_length=255, null=True)
    basis_prev = models.ForeignKey(
        db_column="basis_prevcd",
        to="BasisOfName",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    nmchange = models.ForeignKey(
        db_column="nmchangecd",
        to="NamechangeReason",
        on_delete=models.CASCADE,
        null=True,
    )
    combprod = models.ForeignKey(
        db_column="combprodcd",
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
    )
    pres_stat = models.ForeignKey(
        db_column="pres_statcd",
        to="VirtualProductPresStatus",
        on_delete=models.CASCADE,
    )
    sug_f = models.BooleanField()
    glu_f = models.BooleanField()
    pres_f = models.BooleanField()
    cfc_f = models.BooleanField()
    non_avail = models.ForeignKey(
        db_column="non_availcd",
        to="VirtualProductNonAvail",
        on_delete=models.CASCADE,
        null=True,
    )
    non_availdt = models.DateField(null=True)
    df_ind = models.ForeignKey(
        db_column="df_indcd",
        to="DfIndicator",
        on_delete=models.CASCADE,
        null=True,
    )
    udfs = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    udfs_uom = models.ForeignKey(
        db_column="udfs_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    unit_dose_uom = models.ForeignKey(
        db_column="unit_dose_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )


class VPI(models.Model):
    class Meta:
        db_table = "vpi"

    vmp = models.ForeignKey(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    ing = models.ForeignKey(db_column="isid", to="Ing", on_delete=models.CASCADE)
    basis_strnt = models.ForeignKey(
        db_column="basis_strntcd",
        to="BasisOfStrnth",
        on_delete=models.CASCADE,
        null=True,
    )
    bs_subid = models.BigIntegerField(null=True)
    strnt_nmrtr_val = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    strnt_nmrtr_uom = models.ForeignKey(
        db_column="strnt_nmrtr_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    strnt_dnmtr_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
    )
    strnt_dnmtr_uom = models.ForeignKey(
        db_column="strnt_dnmtr_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )


class Ont(models.Model):
    class Meta:
        db_table = "ont"

    vmp = models.ForeignKey(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    form = models.ForeignKey(
        db_column="formcd",
        to="OntFormRoute",
        on_delete=models.CASCADE,
    )


class Dform(models.Model):
    class Meta:
        db_table = "dform"

    vmp = models.OneToOneField(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    form = models.ForeignKey(db_column="formcd", to="Form", on_delete=models.CASCADE)


class Droute(models.Model):
    class Meta:
        db_table = "droute"

    vmp = models.ForeignKey(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    route = models.ForeignKey(db_column="routecd", to="Route", on_delete=models.CASCADE)


class ControlInfo(models.Model):
    class Meta:
        db_table = "control_info"

    vmp = models.OneToOneField(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    cat = models.ForeignKey(
        db_column="catcd",
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
    )
    catdt = models.DateField(null=True)
    cat_prev = models.ForeignKey(
        db_column="cat_prevcd",
        to="ControlDrugCategory",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )


class AMP(models.Model):
    class Meta:
        db_table = "amp"

    apid = models.BigIntegerField(primary_key=True)
    invalid = models.BooleanField()
    vmp = models.ForeignKey(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    nm = models.CharField(max_length=255)
    abbrevnm = models.CharField(max_length=60, null=True)
    descr = models.CharField(max_length=700)
    nmdt = models.DateField(null=True)
    nm_prev = models.CharField(max_length=255, null=True)
    supp = models.ForeignKey(
        db_column="suppcd",
        to="Supplier",
        on_delete=models.CASCADE,
    )
    lic_auth = models.ForeignKey(
        db_column="lic_authcd",
        to="LicensingAuthority",
        on_delete=models.CASCADE,
    )
    lic_auth_prev = models.ForeignKey(
        db_column="lic_auth_prevcd",
        to="LicensingAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    lic_authchange = models.ForeignKey(
        db_column="lic_authchangecd",
        to="LicensingAuthorityChangeReason",
        on_delete=models.CASCADE,
        null=True,
    )
    lic_authchangedt = models.DateField(null=True)
    combprod = models.ForeignKey(
        db_column="combprodcd",
        to="CombinationProdInd",
        on_delete=models.CASCADE,
        null=True,
    )
    flavour = models.ForeignKey(
        db_column="flavourcd",
        to="Flavour",
        on_delete=models.CASCADE,
        null=True,
    )
    ema = models.BooleanField()
    parallel_import = models.BooleanField()
    avail_restrict = models.ForeignKey(
        db_column="avail_restrictcd",
        to="AvailabilityRestriction",
        on_delete=models.CASCADE,
    )


class LicRoute(models.Model):
    class Meta:
        db_table = "lic_route"

    amp = models.ForeignKey(db_column="apid", to=AMP, on_delete=models.CASCADE)
    route = models.ForeignKey(
        db_column="routecd",
        to="Route",
        on_delete=models.CASCADE,
    )


class ApInfo(models.Model):
    class Meta:
        db_table = "ap_info"

    amp = models.OneToOneField(db_column="apid", to=AMP, on_delete=models.CASCADE)
    sz_weight = models.CharField(max_length=100, null=True)
    colour = models.ForeignKey(
        db_column="colourcd",
        to="Colour",
        on_delete=models.CASCADE,
        null=True,
    )
    prod_order_no = models.CharField(max_length=20, null=True)


class VMPP(models.Model):
    class Meta:
        db_table = "vmpp"

    vppid = models.BigIntegerField(primary_key=True)
    invalid = models.BooleanField()
    nm = models.CharField(max_length=420)
    abbrevnm = models.CharField(max_length=60, null=True)
    vmp = models.ForeignKey(db_column="vpid", to=VMP, on_delete=models.CASCADE)
    qtyval = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    qty_uom = models.ForeignKey(
        db_column="qty_uomcd",
        to="UnitOfMeasure",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
    )


class Dtinfo(models.Model):
    class Meta:
        db_table = "dtinfo"

    vmpp = models.OneToOneField(db_column="vppid", to=VMPP, on_delete=models.CASCADE)
    pay_cat = models.ForeignKey(
        db_column="pay_catcd",
        to="DtPaymentCategory",
        on_delete=models.CASCADE,
    )
    price = models.IntegerField(null=True)
    dt = models.DateField(null=True)
    prevprice = models.IntegerField(null=True)


class AMPP(models.Model):
    class Meta:
        db_table = "ampp"

    appid = models.BigIntegerField(primary_key=True)
    invalid = models.BooleanField()
    nm = models.CharField(max_length=774)
    abbrevnm = models.CharField(max_length=60, null=True)
    vmpp = models.ForeignKey(db_column="vppid", to=VMPP, on_delete=models.CASCADE)
    amp = models.ForeignKey(db_column="apid", to=AMP, on_delete=models.CASCADE)
    combpack = models.ForeignKey(
        db_column="combpackcd",
        to="CombinationPackInd",
        on_delete=models.CASCADE,
        null=True,
    )
    legal_cat = models.ForeignKey(
        db_column="legal_catcd",
        to="LegalCategory",
        on_delete=models.CASCADE,
    )
    subp = models.CharField(max_length=30, null=True)
    disc = models.ForeignKey(
        db_column="disccd",
        to="DiscontinuedInd",
        on_delete=models.CASCADE,
        null=True,
    )
    discdt = models.DateField(null=True)


class PackInfo(models.Model):
    class Meta:
        db_table = "pack_info"

    ampp = models.OneToOneField(db_column="appid", to=AMPP, on_delete=models.CASCADE)
    reimb_stat = models.ForeignKey(
        db_column="reimb_statcd",
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
    )
    reimb_statdt = models.DateField(null=True)
    reimb_statprev = models.ForeignKey(
        db_column="reimb_statprevcd",
        to="ReimbursementStatus",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
    )
    pack_order_no = models.CharField(max_length=20, null=True)


class PrescribInfo(models.Model):
    class Meta:
        db_table = "prescrib_info"

    ampp = models.OneToOneField(db_column="appid", to=AMPP, on_delete=models.CASCADE)
    sched_2 = models.BooleanField()
    acbs = models.BooleanField()
    padm = models.BooleanField()
    fp10_mda = models.BooleanField()
    sched_1 = models.BooleanField()
    hosp = models.BooleanField()
    nurse_f = models.BooleanField()
    enurse_f = models.BooleanField()
    dent_f = models.BooleanField()


class PriceInfo(models.Model):
    class Meta:
        db_table = "price_info"

    ampp = models.OneToOneField(db_column="appid", to=AMPP, on_delete=models.CASCADE)
    price = models.IntegerField(null=True)
    pricedt = models.DateField(null=True)
    price_prev = models.IntegerField(null=True)
    price_basis = models.ForeignKey(
        db_column="price_basiscd",
        to="PriceBasis",
        on_delete=models.CASCADE,
    )


class ReimbInfo(models.Model):
    class Meta:
        db_table = "reimb_info"

    ampp = models.OneToOneField(db_column="appid", to=AMPP, on_delete=models.CASCADE)
    px_chrgs = models.IntegerField(null=True)
    disp_fees = models.IntegerField(null=True)
    bb = models.BooleanField()
    cal_pack = models.BooleanField()
    spec_cont = models.ForeignKey(
        db_column="spec_contcd",
        to="SpecCont",
        on_delete=models.CASCADE,
        null=True,
    )
    dnd = models.ForeignKey(
        # This column is called "dnd" in the raw data, but we rename it to "dndcd" for
        # consistency.
        db_column="dndcd",
        to="Dnd",
        on_delete=models.CASCADE,
        null=True,
    )
    fp34d = models.BooleanField()


class Ing(models.Model):
    class Meta:
        db_table = "ing"

    isid = models.BigIntegerField(primary_key=True)
    isiddt = models.DateField(null=True)
    isidprev = models.BigIntegerField(null=True)
    invalid = models.BooleanField()
    nm = models.CharField(max_length=255)


class CombinationPackInd(models.Model):
    class Meta:
        db_table = "combination_pack_ind"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class CombinationProdInd(models.Model):
    class Meta:
        db_table = "combination_prod_ind"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class BasisOfName(models.Model):
    class Meta:
        db_table = "basis_of_name"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=150)


class NamechangeReason(models.Model):
    class Meta:
        db_table = "namechange_reason"

    cd = models.IntegerField(primary_key=True)
    # Unlike every other lookup table, this can have a null description.
    descr = models.CharField(max_length=150, null=True)


class VirtualProductPresStatus(models.Model):
    class Meta:
        db_table = "virtual_product_pres_status"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class ControlDrugCategory(models.Model):
    class Meta:
        db_table = "control_drug_category"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class LicensingAuthority(models.Model):
    class Meta:
        db_table = "licensing_authority"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class UnitOfMeasure(models.Model):
    class Meta:
        db_table = "unit_of_measure"

    cd = models.BigIntegerField(primary_key=True)
    cddt = models.DateField(null=True)
    cdprev = models.BigIntegerField(null=True)
    descr = models.CharField(max_length=150)


class Form(models.Model):
    class Meta:
        db_table = "form"

    cd = models.BigIntegerField(primary_key=True)
    cddt = models.DateField(null=True)
    cdprev = models.BigIntegerField(null=True)
    descr = models.CharField(max_length=60)


class OntFormRoute(models.Model):
    class Meta:
        db_table = "ont_form_route"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class Route(models.Model):
    class Meta:
        db_table = "route"

    cd = models.BigIntegerField(primary_key=True)
    cddt = models.DateField(null=True)
    cdprev = models.BigIntegerField(null=True)
    descr = models.CharField(max_length=60)


class DtPaymentCategory(models.Model):
    class Meta:
        db_table = "dt_payment_category"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class Supplier(models.Model):
    class Meta:
        db_table = "supplier"

    cd = models.BigIntegerField(primary_key=True)
    cddt = models.DateField(null=True)
    cdprev = models.BigIntegerField(null=True)
    invalid = models.BooleanField()
    descr = models.CharField(max_length=80)


class Flavour(models.Model):
    class Meta:
        db_table = "flavour"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class Colour(models.Model):
    class Meta:
        db_table = "colour"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class BasisOfStrnth(models.Model):
    class Meta:
        db_table = "basis_of_strnth"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=150)


class ReimbursementStatus(models.Model):
    class Meta:
        db_table = "reimbursement_status"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class SpecCont(models.Model):
    class Meta:
        db_table = "spec_cont"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class Dnd(models.Model):
    class Meta:
        db_table = "dnd"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class VirtualProductNonAvail(models.Model):
    class Meta:
        db_table = "virtual_product_non_avail"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class DiscontinuedInd(models.Model):
    class Meta:
        db_table = "discontinued_ind"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class DfIndicator(models.Model):
    class Meta:
        db_table = "df_indicator"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=20)


class PriceBasis(models.Model):
    class Meta:
        db_table = "price_basis"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class LegalCategory(models.Model):
    class Meta:
        db_table = "legal_category"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class AvailabilityRestriction(models.Model):
    class Meta:
        db_table = "availability_restriction"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)


class LicensingAuthorityChangeReason(models.Model):
    class Meta:
        db_table = "licensing_authority_change_reason"

    cd = models.IntegerField(primary_key=True)
    descr = models.CharField(max_length=60)
