from openprescribing.data.models import (
    VMP,
    VPI,
    VTM,
    BasisOfName,
    BNFCode,
    DmdBnfMap,
    Ing,
    Ont,
    OntFormRoute,
    VirtualProductPresStatus,
)


class MedicationsBuilder:
    """This class supports populating the rxdb medications view by inserting data into
    the underlying tables.

    It can be used in tests via the medications fixture.

    At the moment we only support adding VMPs.  Adding AMPs would be straightforward.
    """

    def __init__(self):
        self._next_id = 1
        self._next_form_route_cd = 1
        self._form_route_cds = {}

    def add_rows(self, rows):
        """This method should be called in tests to populate the underlying tables."""

        # There are non-nullable FKs from VMP to these tables, so we need to have
        # records in the database.
        BasisOfName.objects.get_or_create(cd=0, defaults={"descr": ""})
        VirtualProductPresStatus.objects.get_or_create(cd=0, defaults={"descr": ""})

        for row in rows:
            self._add_row(**row)

    def _add_row(
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
