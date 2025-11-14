import altair as alt
from django.shortcuts import render

from openprescribing.data import rxdb
from openprescribing.data.models import BNFCode


def index(request):
    bnf_code = BNFCode.objects.get(code="0601023AW")  # Semaglutide

    sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE bnf_code LIKE '{bnf_code.code}%'
    """

    with rxdb.get_cursor() as cursor:
        pdm = rxdb.get_practice_date_matrix(cursor, sql)

    dates = pdm.col_labels
    values = pdm.values.sum(axis=0)

    chart_data = [
        {"month": date.isoformat(), "items": value}
        for date, value in zip(dates, values)
    ]

    chart_data.sort(key=lambda row: row["month"])

    chart = (
        alt.Chart(data=alt.Data(values=chart_data))
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("items:Q", title="Items"),
            tooltip=[
                alt.Tooltip("month:T", title="Month", format="%b %Y"),
                alt.Tooltip("items:Q", title="Items", format=","),
            ],
        )
        .properties(width=1200, height=360)
    )

    ctx = {"bnf_code": bnf_code, "chart_spec": chart.to_json()}

    return render(request, "index.html", ctx)
