import altair as alt


def build_chart_spec(dtr_is_list_size):
    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y("value:Q", title="Items per 1000 patents" if dtr_is_list_size else "%")
    stroke_width = (
        alt.when(alt.datum.centile == 50).then(alt.value(3)).otherwise(alt.value(1))
    )
    deciles_chart = (
        alt.Chart(alt.NamedData("deciles"))
        .mark_line(color="#3182BD")
        .encode(x=x, y=y, detail="centile:O", strokeWidth=stroke_width)
        .properties(width=660, height=360)
    )
    all_orgs_line_chart = (
        alt.Chart(alt.NamedData("all_orgs_line_chart"))
        .mark_line(color="grey", opacity=0.2)
        .encode(x=x, y=y, detail="org:O")
        .properties(width=660, height=360)
    )
    deciles_chart += all_orgs_line_chart

    all_orgs_dots_chart = (
        alt.Chart(alt.NamedData("all_orgs_dots_chart"))
        .mark_point(color="grey", opacity=0.3, filled=True)
        .encode(
            x="x_jitter:T",
            y=y,
            detail="org:O",
        )
        # 14 days in ms = 14*24*60*60*1000 = 1209600000
        .transform_calculate(x_jitter="time(datum.month)+(random()*1209600000)")
        .properties(width=660, height=360)
    )
    deciles_chart += all_orgs_dots_chart

    # Org line should go on top of any other charts
    org_chart = (
        alt.Chart(alt.NamedData("org"))
        .mark_line(color="#DE2D26", strokeWidth=3)
        .encode(x=x, y=y)
    )
    deciles_chart += org_chart

    return deciles_chart.to_dict()
