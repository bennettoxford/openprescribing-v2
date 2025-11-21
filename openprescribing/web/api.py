import altair as alt
from django.http import JsonResponse

from openprescribing.data import rxdb
from openprescribing.data.models import BNFCode, Org

from .deciles import build_deciles_chart_df


def prescribing(request):
    code = request.GET.get("code")
    org_id = request.GET.get("org_id")
    bnf_code = BNFCode.objects.get(code=code)

    ntr_sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE bnf_code LIKE '{bnf_code.code}%'
    """

    dtr_sql = "SELECT practice_id, date_id, total / 1000 AS value FROM list_size"

    with rxdb.get_cursor() as cursor:
        # We currently have about 8 years (96 months) of list size data.
        ntr_pdm = rxdb.get_practice_date_matrix(cursor, ntr_sql, date_count=96)
        dtr_pdm = rxdb.get_practice_date_matrix(cursor, dtr_sql, date_count=96)

    pdm = ntr_pdm / dtr_pdm

    practices = Org.objects.filter(org_type=Org.OrgType.PRACTICE)
    pdm = pdm.group_rows(practices.with_practice_ids())

    if org_id is not None:
        org = Org.objects.get(id=org_id)
    else:
        org = None
    chart_df = build_deciles_chart_df(pdm, org)

    chart = (
        alt.Chart(chart_df)
        .mark_line()
        .encode(
            x=alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b")),
            y=alt.Y("value:Q", title="Items per 1000 patients"),
            detail="line",
            strokeDash=alt.StrokeDash("dash:N", legend=None, scale=None),
            color=alt.Color("colour:N", legend=None, scale=None),
        )
        .properties(width=660, height=360)
    )

    return JsonResponse(chart.to_dict())
