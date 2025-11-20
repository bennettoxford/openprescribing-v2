import altair as alt
from django.http import JsonResponse

from openprescribing.data import rxdb
from openprescribing.data.models import BNFCode, Org

from .deciles import build_deciles_chart_df


def prescribing(request):
    code = request.GET.get("code")
    practice_id = request.GET.get("practice_id")
    bnf_code = BNFCode.objects.get(code=code)

    sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE bnf_code LIKE '{bnf_code.code}%'
    """

    with rxdb.get_cursor() as cursor:
        pdm = rxdb.get_practice_date_matrix(cursor, sql)

    rlm = (
        (org.id, (org.id,)) for org in Org.objects.filter(org_type=Org.OrgType.PRACTICE)
    )
    pdm = pdm.group_rows(rlm)

    chart_df = build_deciles_chart_df(pdm, practice_id)

    chart = (
        alt.Chart(chart_df)
        .mark_line()
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("value:Q", title="Items"),
            detail="line",
            strokeDash=alt.StrokeDash("dash:N", legend=None, scale=None),
            color=alt.Color("colour:N", legend=None, scale=None),
        )
        .properties(width=660, height=360)
    )

    return JsonResponse(chart.to_dict())
