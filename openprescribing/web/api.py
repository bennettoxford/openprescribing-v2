import altair as alt
from django.http import JsonResponse

from openprescribing.data import rxdb
from openprescribing.data.models import Org
from openprescribing.data.rxdb.search import ProductType, search
from openprescribing.data.utils.deciles_utils import build_deciles_df, build_org_df


def prescribing_deciles(request):
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
        title = "%"
    else:
        dtr_sql = "SELECT practice_id, date_id, total AS value FROM list_size"
        multiplier = 1000
        title = "Items per 1000 patients"

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
        org_type = Org.OrgType.PRACTICE

    org_to_practice_ids = Org.objects.filter(org_type=org_type).with_practice_ids()

    ntr_odm = ntr_pdm.group_rows(org_to_practice_ids)
    dtr_odm = dtr_pdm.group_rows(org_to_practice_ids)

    odm = ntr_odm / dtr_odm * multiplier

    deciles_df = build_deciles_df(odm)
    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y("value:Q", title=title)
    stroke_dash = (
        alt.when(alt.datum.line == "p50")
        .then(alt.value((6, 2)))
        .otherwise(alt.value((2, 6)))
    )
    deciles_chart = (
        alt.Chart(deciles_df)
        .mark_line(color="blue")
        .encode(x=x, y=y, detail="line", strokeDash=stroke_dash)
        .properties(width=660, height=360)
    )

    if org is not None:
        org_df = build_org_df(odm, org)
        org_chart = alt.Chart(org_df).mark_line(color="red").encode(x=x, y=y)
        chart = deciles_chart + org_chart
    else:
        chart = deciles_chart

    return JsonResponse(chart.to_dict())
