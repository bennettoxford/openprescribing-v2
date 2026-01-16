import altair as alt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from openprescribing.data import rxdb
from openprescribing.data.models import BNFCode, Org

from .deciles import build_deciles_chart_df


def prescribing_deciles(request):
    codes = request.GET.get("codes").split(",")

    org_id = request.GET.get("org_id")
    bnf_codes_inclusion = []
    bnf_codes_exclusion = []
    for code in codes:
        if code[0] == "-":
            bnf_codes_exclusion.append(get_object_or_404(BNFCode, code=code[1:]))
        else:
            bnf_codes_inclusion.append(get_object_or_404(BNFCode, code=code))

    inclusion_clause = " OR ".join(
        [f"bnf_code LIKE '{bnf_code.code}%'" for bnf_code in bnf_codes_inclusion]
    )
    if bnf_codes_exclusion:
        exclusion_clause = " AND NOT " + " OR ".join(
            [f"bnf_code LIKE '{bnf_code.code}%'" for bnf_code in bnf_codes_exclusion]
        )
    else:
        exclusion_clause = ""

    ntr_sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE {inclusion_clause} {exclusion_clause}
    """

    org_id = request.GET.get("org_id")

    dtr_sql = "SELECT practice_id, date_id, total / 1000 AS value FROM list_size"

    with rxdb.get_cursor() as cursor:
        # We currently have about 8 years (96 months) of list size data.
        ntr_pdm = rxdb.get_practice_date_matrix(cursor, ntr_sql, date_count=96)
        dtr_pdm = rxdb.get_practice_date_matrix(cursor, dtr_sql, date_count=96)

    if org_id is not None:
        org = Org.objects.get(id=org_id)
        org_type = org.org_type
    else:
        org = None
        org_type = Org.OrgType.PRACTICE

    org_to_practice_ids = Org.objects.filter(org_type=org_type).with_practice_ids()

    ntr_odm = ntr_pdm.group_rows(org_to_practice_ids)
    dtr_odm = dtr_pdm.group_rows(org_to_practice_ids)

    odm = ntr_odm / dtr_odm

    chart_df = build_deciles_chart_df(odm, org)

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
