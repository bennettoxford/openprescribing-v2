import altair as alt

from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery


def build_org_chart_spec(analysis):
    if not analysis:
        return

    if isinstance(analysis.dtr_query, BNFQuery):
        title = "%"
    else:
        assert isinstance(analysis.dtr_query, ListSizeQuery)
        title = "Items per 1000 patients"

    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y("value:Q", title=title)
    stroke_width = (
        alt.when(alt.datum.centile == 50).then(alt.value(3)).otherwise(alt.value(1))
    )
    chart_spec = (
        alt.Chart(alt.NamedData("deciles"))
        .mark_line(color="#3182BD")
        .encode(x=x, y=y, detail="centile:O", strokeWidth=stroke_width)
    )
    all_orgs_line_chart = (
        alt.Chart(alt.NamedData("all_orgs_line"))
        .mark_line(color="grey", opacity=0.2)
        .encode(x=x, y=y, detail="org:O")
    )
    chart_spec += all_orgs_line_chart

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
    chart_spec += all_orgs_dots_chart

    # Org line should go on top of any other charts
    org_chart = (
        alt.Chart(alt.NamedData("org"))
        .mark_line(color="#DE2D26", strokeWidth=3)
        .encode(x=x, y=y)
    )
    chart_spec += org_chart

    chart_spec = chart_spec.configure(
        autosize={"type": "fit", "resize": True}
    ).properties(width="container", height=360)

    return chart_spec.to_dict()


def build_medications_chart_spec(analysis):
    """Build the spec for the "by medication" stacked area chart.

    Unlike the deciles/all-orgs charts this shows absolute item counts (not a ratio)
    broken down by medication, so it needs its own y-axis and colour legend.  We
    therefore give it a separate spec which the frontend embeds in place of the combined
    chart, rather than adding it as a layer to that chart (which would leak its axis and
    legend onto the other chart types).
    """
    if not analysis:
        return

    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    chart_spec = (
        alt.Chart(alt.NamedData("medications"))
        .mark_area()
        .transform_joinaggregate(medication_total="sum(value)", groupby=["medication"])
        .transform_joinaggregate(max_medication_total="max(medication_total)")
        # Stack "Other" at the bottom, then the named medications largest-first so the
        # smallest ends up at the top.  Driving both the stack `order` and the colour
        # legend `sort` from this one field keeps the legend in the same order as the
        # areas.
        .transform_calculate(
            stack_order=(
                "datum.medication === 'Other' ? -1"
                " : datum.max_medication_total - datum.medication_total"
            )
        )
        .encode(
            x=x,
            y=alt.Y("value:Q", title="Items", stack="zero"),
            color=alt.Color(
                "medication:N",
                title="Medication",
                sort=alt.EncodingSortField(
                    field="stack_order", op="max", order="descending"
                ),
            ),
            order=alt.Order("stack_order:Q"),
            tooltip=[
                alt.Tooltip("medication:N", title="Medication"),
                alt.Tooltip("month:T", title="Month", format="%Y %b"),
                alt.Tooltip("value:Q", title="Items"),
            ],
        )
    )

    chart_spec = chart_spec.configure(
        autosize={"type": "fit", "resize": True}
    ).properties(width="container", height=360)

    return chart_spec.to_dict()
