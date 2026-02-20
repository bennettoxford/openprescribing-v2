import math

from django.http import JsonResponse
from django.views.decorators.cache import cache_control

from openprescribing.data import rxdb
from openprescribing.data.models import Org
from openprescribing.data.rxdb.search import ProductType, search
from openprescribing.data.utils.deciles_utils import (
    build_all_orgs_df,
    build_deciles_df,
    build_org_df,
)


def _build_odm(request):
    ntr_query = request.GET.get("ntr_codes").split(",")
    ntr_product_type = ProductType(request.GET.get("ntr_product_type", "all"))
    ntr_codes = search(ntr_query, ntr_product_type)

    ntr_sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE bnf_code IN ({", ".join(f"'{c}'" for c in ntr_codes)})
    """

    if "dtr_codes" in request.GET:
        dtr_query = request.GET.get("dtr_codes").split(",")
        dtr_product_type = ProductType(request.GET.get("dtr_product_type", "all"))
        dtr_codes = search(dtr_query, dtr_product_type)

        dtr_sql = f"""
        SELECT practice_id, date_id, items AS value
        FROM prescribing
        WHERE bnf_code IN ({", ".join(f"'{c}'" for c in dtr_codes)})
        """
        multiplier = 100
    else:
        dtr_sql = "SELECT practice_id, date_id, total AS value FROM list_size"
        multiplier = 1000

    with rxdb.get_cursor() as cursor:
        # We currently have about 8 years (96 months) of list size data.
        ntr_pdm = rxdb.get_practice_date_matrix(cursor, ntr_sql, date_count=96)
        dtr_pdm = rxdb.get_practice_date_matrix(cursor, dtr_sql, date_count=96)

    org_id = request.GET.get("org_id")

    if org_id is not None:
        org = Org.objects.get(id=org_id)
        org_type = org.org_type
    else:
        org = None
        org_type = Org.OrgType.ICB

    org_to_practice_ids = Org.objects.filter(org_type=org_type).with_practice_ids()

    ntr_odm = ntr_pdm.group_rows(org_to_practice_ids)
    dtr_odm = dtr_pdm.group_rows(org_to_practice_ids)

    odm = ntr_odm / dtr_odm * multiplier

    return odm, org


@cache_control(public=True, max_age=3600)
def prescribing_all_orgs(request):
    odm, _ = _build_odm(request)

    all_orgs_records = build_all_orgs_df(odm).to_dict("records")
    nans_to_nones(all_orgs_records)

    return JsonResponse(
        {"all_orgs": all_orgs_records},
        json_dumps_params={"allow_nan": False},
    )


@cache_control(public=True, max_age=3600)
def prescribing_deciles(request):
    odm, org = _build_odm(request)

    deciles_records = build_deciles_df(odm).to_dict("records")
    if org is not None:
        org_records = build_org_df(odm, org).to_dict("records")
        # The organisation-date matrix (odm) can contain NaNs. NaNs are ignored when
        # deciles are computed, and so are not present in deciles_records. However,
        # NaNs are present in org_records. Python's json.JSONEncoder will serialise
        # NaNs, but JavaScript's JSON.parse won't deserialise them. Consequently, we
        # have to convert NaNs to Nones ourselves.
        nans_to_nones(org_records)
    else:
        org_records = []

    return JsonResponse(
        {"deciles": deciles_records, "org": org_records},
        json_dumps_params={"allow_nan": False},
    )


def nans_to_nones(records):
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
