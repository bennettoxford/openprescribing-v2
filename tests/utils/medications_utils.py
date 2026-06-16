from openprescribing.data.models import (
    AMP,
    VMP,
    VPI,
    VTM,
    AvailabilityRestriction,
    BasisOfName,
    BNFCode,
    DmdBnfMap,
    Ing,
    LicensingAuthority,
    Ont,
    OntFormRoute,
    Supplier,
    VirtualProductPresStatus,
)


class MedicationsBuilder:
    """This class supports populating the rxdb medications view by inserting data into
    the underlying tables.

    It can be used in tests via the medications fixture.
    """

    def __init__(self):
        self._next_id = 1
        self._next_form_route_cd = 1
        self._form_route_cds = {}

    def add_rows(self, rows):
        """This method should be called in tests to populate the underlying tables.

        Each row is a dict describing either a VMP or an AMP.  A row with a truthy
        `is_amp` key is added as an AMP belonging to an existing VMP (identified by its
        `vmp_id`); any other row is added as a VMP.
        """

        # There are non-nullable FKs from VMP to these tables, so we need to have
        # records in the database.
        BasisOfName.objects.get_or_create(cd=0, defaults={"descr": ""})
        VirtualProductPresStatus.objects.get_or_create(cd=0, defaults={"descr": ""})

        for row in rows:
            row = dict(row)
            if row.pop("is_amp", False):
                self._add_amp(**row)
            else:
                self._add_vmp(**row)

    def _add_vmp(
        self,
        *,
        bnf_code=None,
        name="",
        invalid=False,
        vtm_id=None,
        ingredient_ids=(),
        form_routes=(),
    ):
        dmd_id = self._next_id
        self._next_id += 1

        BNFCode.objects.get_or_create(
            code=bnf_code,
            defaults={"name": "", "level": BNFCode.Level.PRESENTATION},
        )

        DmdBnfMap.objects.create(dmd_id=dmd_id, bnf_code=bnf_code)

        if vtm_id is not None:
            VTM.objects.get_or_create(
                vtmid=vtm_id, defaults={"nm": "", "invalid": False}
            )

        VMP.objects.create(
            vpid=dmd_id,
            nm=name,
            vtm_id=vtm_id,
            invalid=invalid,
            basis_id=0,
            pres_stat_id=0,
            sug_f=False,
            glu_f=False,
            pres_f=False,
            cfc_f=False,
        )

        for isid in ingredient_ids:
            Ing.objects.get_or_create(isid=isid, defaults={"nm": "", "invalid": False})
            VPI.objects.create(vmp_id=dmd_id, ing_id=isid)

        for descr in form_routes:
            formcd = self._get_or_create_form_route_cd(descr)
            Ont.objects.create(vmp_id=dmd_id, form_id=formcd)

    def _add_amp(self, *, vmp_id, bnf_code=None, name="", invalid=False):
        # There are non-nullable FKs from AMP to these tables, so we need to have
        # records in the database.
        Supplier.objects.get_or_create(cd=0, defaults={"descr": "", "invalid": False})
        LicensingAuthority.objects.get_or_create(cd=0, defaults={"descr": ""})
        AvailabilityRestriction.objects.get_or_create(cd=0, defaults={"descr": ""})

        apid = self._next_id
        self._next_id += 1

        # An AMP shares its VMP's BNF code unless one is given explicitly.
        if bnf_code is None:  # pragma: no cover
            bnf_code = DmdBnfMap.objects.get(dmd_id=vmp_id).bnf_code

        BNFCode.objects.get_or_create(
            code=bnf_code,
            defaults={"name": "", "level": BNFCode.Level.PRESENTATION},
        )

        DmdBnfMap.objects.create(dmd_id=apid, bnf_code=bnf_code)

        AMP.objects.create(
            apid=apid,
            vmp_id=vmp_id,
            nm=name,
            descr=name,
            invalid=invalid,
            supp_id=0,
            lic_auth_id=0,
            avail_restrict_id=0,
            ema=False,
            parallel_import=False,
        )

    def _get_or_create_form_route_cd(self, descr):
        # Assign a stable cd to each form/route description so that the medications
        # view stores numeric ids (as in production) while tests can supply and query
        # by description.
        if descr not in self._form_route_cds:
            formcd = self._next_form_route_cd
            self._next_form_route_cd += 1
            self._form_route_cds[descr] = formcd
            OntFormRoute.objects.get_or_create(cd=formcd, defaults={"descr": descr})
        return self._form_route_cds[descr]
