import json
import math

import numpy as np
from django.http import JsonResponse as DjangoJsonResponse

from openprescribing.data import rxdb
from openprescribing.data.analysis import Analysis
from openprescribing.data.models import BNFCode, Org
from openprescribing.data.queries import (
    get_medication_date_matrix,
    get_org_date_ratio_matrix,
)
from openprescribing.web.decorators import add_cache_headers, cache


# We currently have about 8 years (96 months) of list size data.  In future we could
# allow this to be configured by the user, or calculated directly from the data.
DATE_COUNT = 96

# The number of individual medications shown as their own band in the "by medication"
# stacked area chart.  Any further medications are summed into a single "Other" band.
MEDICATIONS_TOP_N = 10

# Selects medications that have been prescribed: VMPs/AMPs whose BNF code appears in the
# prescribing data, plus the parent VMPs of any prescribed AMPs.
PRESCRIBED_MEDICATIONS_SQL = """
    SELECT * FROM medications
    WHERE bnf_code IN (SELECT bnf_code FROM presentation)
    OR (
        NOT is_amp
        AND id IN (
            SELECT DISTINCT vmp_id FROM medications
            WHERE is_amp AND bnf_code IN (SELECT bnf_code FROM presentation)
        )
    )
"""


def _get_org(analysis):
    org_id = analysis.org_id

    if org_id is not None:
        return Org.objects.get(id=org_id)
    else:
        return None


def _get_org_records(odm, org):
    if org is not None:
        org_records = [
            {"month": month, "value": value}
            for month, value in zip(odm.col_labels, odm.get_row(org.id))
        ]
        # The organisation-date matrix (odm) can contain NaNs. NaNs are ignored when
        # deciles are computed, and so are not present in deciles_records. However,
        # NaNs are present in org_records. Python's json.JSONEncoder will serialise
        # NaNs, but JavaScript's JSON.parse won't deserialise them. Consequently, we
        # have to convert NaNs to Nones ourselves.
        nans_to_nones(org_records)
    else:
        org_records = []

    return org_records


def prescribing_all_orgs(request):
    analysis = Analysis.from_dict(json.loads(request.GET["analysis"]))

    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis, date_count=DATE_COUNT)
    org = _get_org(analysis)

    all_orgs_records = list(odm.to_records(row_name="org", col_name="month"))
    nans_to_nones(all_orgs_records)
    org_records = _get_org_records(odm, org)

    return JsonResponse({"all_orgs": all_orgs_records, "org": org_records})


def prescribing_deciles(request):
    analysis = Analysis.from_dict(json.loads(request.GET["analysis"]))

    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis, date_count=DATE_COUNT)
    org = _get_org(analysis)
    cdm = odm.get_centiles()

    deciles_records = list(cdm.to_records(row_name="centile", col_name="month"))
    org_records = _get_org_records(odm, org)

    return JsonResponse({"deciles": deciles_records, "org": org_records})


def prescribing_medications(request):
    """Return national prescribing for the numerator query, broken down by medication.

    The breakdown is limited to the `MEDICATIONS_TOP_N` medications with the most
    prescribing, with any remaining medications summed into a single "Other" band.  This
    keeps the resulting stacked area chart (and its legend) readable.
    """
    analysis = Analysis.from_dict(json.loads(request.GET["analysis"]))

    with rxdb.get_cursor() as cursor:
        mdm = get_medication_date_matrix(
            cursor, analysis.ntr_query, date_count=DATE_COUNT
        )

    row_label_map = _get_top_n_row_label_map(mdm, MEDICATIONS_TOP_N)
    grouped = mdm.group_rows(row_label_map)

    medications_records = list(
        grouped.to_records(row_name="medication", col_name="month")
    )
    numpy_scalars_to_native_types(medications_records)
    nans_to_nones(medications_records)

    return JsonResponse({"medications": medications_records})


def _get_top_n_row_label_map(mdm, n):
    """Build a `group_rows` mapping that keeps the top N medications by total prescribing
    and rolls the remainder into a single "Other" group.

    The matrix rows are presentation-level BNF codes, which we relabel with their
    human-readable names.  The "Other" group is placed last so it stacks at the bottom of
    the chart.
    """
    totals = np.nansum(mdm.values, axis=1)
    # Order row indices by total prescribing, largest first.
    ordered_indexes = np.argsort(totals)[::-1]
    top_indexes = ordered_indexes[:n]
    rest_indexes = ordered_indexes[n:]

    top_codes = [mdm.row_labels[i] for i in top_indexes]
    code_to_name = dict(
        BNFCode.objects.filter(code__in=top_codes).values_list("code", "name")
    )

    row_label_map = [(code_to_name[code], (code,)) for code in top_codes]
    if len(rest_indexes):
        rest_codes = tuple(mdm.row_labels[i] for i in rest_indexes)
        row_label_map.append(("Other", rest_codes))

    return tuple(row_label_map)


@add_cache_headers
def metadata_medications(request):
    return JsonResponse(_metadata_medications_payload())


@cache
def _metadata_medications_payload():
    """Return details of all medications that have been prescribed.

    Include VMPs for any prescribed AMPs, even if the VMP itself has not been
    prescribed.
    """
    with rxdb.get_cursor() as cursor:
        medications = (
            cursor.sql(PRESCRIBED_MEDICATIONS_SQL).to_arrow_table().to_pylist()
        )
    return {"medications": medications}


@add_cache_headers
def metadata_dmd(request):
    return JsonResponse(_metadata_dmd_payload())


@cache
def _metadata_dmd_payload():
    """Return details of the dm+d objects relating to prescribed medications.

    This will be used to query and display medications.
    """

    queries = {
        "vtm": """
            SELECT vtm.vtmid AS id, vtm.nm AS name
            FROM vtm
            WHERE vtm.vtmid IN (
                SELECT vtm_id FROM prescribed WHERE vtm_id IS NOT NULL
            )
        """,
        "vmp": "SELECT id, vtm_id, name FROM prescribed WHERE NOT is_amp",
        "amp": "SELECT id, vmp_id, name FROM prescribed WHERE is_amp",
        "ingredient": """
            SELECT DISTINCT ing.isid AS id, ing.nm AS name
            FROM ing
            JOIN vpi ON vpi.isid = ing.isid
            WHERE vpi.vpid IN (SELECT vmp_id FROM prescribed)
        """,
        "ont_form_route": """
            SELECT DISTINCT ont_form_route.cd AS id, ont_form_route.descr AS descr
            FROM ont_form_route
            JOIN ont ON ont.formcd = ont_form_route.cd
            WHERE ont.vpid IN (SELECT vmp_id FROM prescribed)
        """,
    }
    payload = {}
    with rxdb.get_cursor() as cursor:
        for key, sql in queries.items():
            full_sql = f"WITH prescribed AS ({PRESCRIBED_MEDICATIONS_SQL}) {sql}"
            payload[key] = cursor.sql(full_sql).to_arrow_table().to_pylist()
    return payload


@add_cache_headers
def metadata_bnf(request):
    return JsonResponse(_metadata_bnf_payload())


@cache
def _metadata_bnf_payload():
    """Return details of BNF objects that will be used to query and display
    medications.

    In order to handle strength and formulation equivalents, we replace the records for
    level 6 objects (ie BNF products) with records for strength and formulation
    equivalents.

    Chapters 20 to 23 (devices rather than medicines) have a slightly different code
    structure, and so will need to be handled slightly differently. k
    """

    base_queryset = BNFCode.objects.exclude(code__startswith="2").order_by(
        "level", "code"
    )
    strength_and_formulation_records = [
        {
            "code": code.strength_and_formulation_code,
            "level": 6,
            "name": code.strength_and_formulation_name,
        }
        for code in base_queryset.filter(level=BNFCode.Level.PRESENTATION)
        if code.is_generic()
    ]
    records = (
        list(base_queryset.filter(level__lte=BNFCode.Level.CHEMICAL_SUBSTANCE).values())
        + strength_and_formulation_records
        + list(base_queryset.filter(level=BNFCode.Level.PRESENTATION).values())
    )
    return {"bnf": records}


class JsonResponse(DjangoJsonResponse):
    def __init__(self, *args, **kwargs):
        kwargs["json_dumps_params"] = {"allow_nan": False}
        super().__init__(*args, **kwargs)


def nans_to_nones(records):
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None


def numpy_scalars_to_native_types(records):
    """Convert any NumPy scalars in `records` to native Python types, in place.

    `JsonResponse` can serialise NumPy scalars that subclass a native type (eg
    `np.float64`, which is a `float`), but not those that don't (eg `np.int64`, which
    is not an `int`).

    Matrices of integer counts -- such as the summed prescribing returned by
    `to_records` in `prescribing_medications` -- therefore yield values that
    `JsonResponse` cannot serialise.  Call this on such records before passing them to
    `JsonResponse`.  It is unnecessary for the ratio endpoints, whose values are already
    `np.float64`.
    """
    for record in records:
        for key, value in record.items():
            if isinstance(value, np.generic):
                record[key] = value.item()
