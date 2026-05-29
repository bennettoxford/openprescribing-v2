import altair as alt

from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery


def build_chart_spec(analysis):
    if analysis and isinstance(analysis.dtr_query, BNFQuery):
        title = "%"
    else:
        if analysis:
            assert isinstance(analysis.dtr_query, ListSizeQuery)
        title = "Items per 1000 patients"

    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y("value:Q", title=title)
    stroke_width = (
        alt.when(alt.datum.centile == 50).then(alt.value(3)).otherwise(alt.value(1))
    )
    deciles_chart = (
        alt.Chart(alt.NamedData("deciles"))
        .mark_line(color="#3182BD")
        .encode(x=x, y=y, detail="centile:O", strokeWidth=stroke_width)
    )
    all_orgs_line_chart = (
        alt.Chart(alt.NamedData("all_orgs_line"))
        .mark_line(color="grey", opacity=0.2)
        .encode(x=x, y=y, detail="org:O")
    )
    deciles_chart += all_orgs_line_chart

    all_orgs_dots_chart = (
        alt.Chart(alt.NamedData("all_orgs_dots"))
        .mark_point(color="grey", opacity=0.3, filled=True)
        .encode(
            x="x_jitter:T",
            y=y,
            detail="org:O",
        )
        # 14 days in ms = 14*24*60*60*1000 = 1209600000
        .transform_calculate(x_jitter="time(datum.month)+(random()*1209600000)")
    )
    deciles_chart += all_orgs_dots_chart

    # Org line should go on top of any other charts
    org_chart = (
        alt.Chart(alt.NamedData("org"))
        .mark_line(color="#DE2D26", strokeWidth=3)
        .encode(x=x, y=y)
    )
    deciles_chart += org_chart

    deciles_chart = deciles_chart.configure(
        autosize={"type": "fit", "resize": True}
    ).properties(width="container", height=360)

    return deciles_chart.to_dict()
