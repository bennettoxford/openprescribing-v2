import json
import math

from django.http import JsonResponse as DjangoJsonResponse

from openprescribing.data import rxdb
from openprescribing.data.analysis import Analysis
from openprescribing.data.models import AMP, VMP, VTM, BNFCode, Ing, OntFormRoute, Org
from openprescribing.data.queries import get_org_date_ratio_matrix


# We currently have about 8 years (96 months) of list size data.  In future we could
# allow this to be configured by the user, or calculated directly from the data.
DATE_COUNT = 96


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
    analysis = Analysis.from_params(request.GET)
    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis, date_count=DATE_COUNT)
    org = _get_org(analysis)

    all_orgs_records = list(odm.to_records(row_name="org", col_name="month"))
    nans_to_nones(all_orgs_records)
    org_records = _get_org_records(odm, org)

    if org is None:
        org_type = "icb"
    else:
        org_type = org.org_type

    return JsonResponse(
        {"all_orgs": all_orgs_records, "org": org_records, "org_type": org_type}
    )


def prescribing_deciles(request):
    if "analysis" in request.GET:
        analysis = Analysis.from_dict(json.loads(request.GET["analysis"]))
    else:
        analysis = Analysis.from_params(request.GET)

    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis, date_count=DATE_COUNT)
    org = _get_org(analysis)
    cdm = odm.get_centiles()

    deciles_records = list(cdm.to_records(row_name="centile", col_name="month"))
    org_records = _get_org_records(odm, org)

    if org is None:
        org_type = "icb"
    else:
        org_type = org.org_type

    return JsonResponse(
        {"deciles": deciles_records, "org": org_records, "org_type": org_type}
    )


def metadata_medications(request):
    """Return details of all medications that have been prescribed.

    Include VMPs for any prescribed AMPs, even if the VMP itself has not been
    prescribed.
    """
    with rxdb.get_cursor() as cursor:
        medications = (
            cursor.sql(
                """
                SELECT * FROM medications
                WHERE bnf_code IN (
                    SELECT bnf_code FROM presentation
                )
                OR (
                    NOT is_amp
                    AND id IN (
                        SELECT DISTINCT vmp_id
                        FROM medications
                        WHERE is_amp
                        AND bnf_code IN (
                            SELECT bnf_code FROM presentation
                        )
                    )
                )
                """
            )
            .to_arrow_table()
            .to_pylist()
        )
    return JsonResponse({"medications": medications})


def metadata_dmd(request):
    """Return details of dm+d objects that will be used to query and display
    medications."""

    payload = {
        "vtm": VTM.objects.api_values(),
        "vmp": VMP.objects.api_values(),
        "amp": AMP.objects.api_values(),
        "ingredient": Ing.objects.api_values(),
        "ont_form_route": OntFormRoute.objects.api_values(),
    }
    return JsonResponse(payload)


def metadata_bnf(request):
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
    return JsonResponse({"bnf": records})


class JsonResponse(DjangoJsonResponse):
    def __init__(self, *args, **kwargs):
        kwargs["json_dumps_params"] = {"allow_nan": False}
        super().__init__(*args, **kwargs)


def nans_to_nones(records):
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
