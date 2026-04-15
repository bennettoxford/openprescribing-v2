from urllib.parse import urlencode

import altair as alt
import markdown
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from openprescribing.data.analysis import Analysis
from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.measures import all_measure_details, load_measure
from openprescribing.data.models import BNFCode, Org

from .analysis_presentation import AnalysisPresentation
from .models import Feedback
from .presenters import (
    make_bnf_table,
    make_bnf_tree,
    make_code_to_name,
    make_ntr_dtr_intersection_table,
    make_orgs,
)


def _build_analysis_context(analysis):
    deciles_api_url = None
    all_orgs_api_url = None
    org = None
    ntr_dtr_intersection_table = None

    if analysis is not None:
        if analysis.org_id:
            org = get_object_or_404(Org, id=analysis.org_id)

        if isinstance(analysis.dtr_query, BNFQuery):
            ntr_dtr_intersection_table = make_ntr_dtr_intersection_table(
                analysis.ntr_query, analysis.dtr_query
            )
        else:
            ntr_dtr_intersection_table = make_ntr_dtr_intersection_table(
                analysis.ntr_query, None
            )

        url_parameters = urlencode(analysis.to_params(), safe=",")
        deciles_api_url = f"{reverse('api_prescribing_deciles')}?{url_parameters}"
        all_orgs_api_url = f"{reverse('api_prescribing_all_orgs')}?{url_parameters}"

    orgs = make_orgs()

    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y(
        "value:Q",
        title="%"
        if analysis and isinstance(analysis.dtr_query, BNFQuery)
        else "Items per 1000 patients",
    )
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

    ctx = {
        "analysis": analysis,
        "ntr_dtr_intersection_table": ntr_dtr_intersection_table,
        "org": org,
        "orgs": orgs,
        "org_types": Org.OrgType.choices,
        "prescribing_deciles_url": deciles_api_url,
        "prescribing_all_orgs_url": all_orgs_api_url,
        "deciles_chart": deciles_chart.to_dict(),
    }

    return ctx


def analysis(request):
    analysis_presentation = AnalysisPresentation.from_params(request.GET)

    if "ntr_codes" in request.GET:
        analysis = Analysis.from_params(request.GET)
    else:
        analysis = None

    ctx = _build_analysis_context(analysis)
    ctx["measure"] = False
    ctx["analysis_presentation"] = analysis_presentation

    return render(request, "analysis.html", ctx)


def build_analysis(request):
    if "ntr_codes" in request.GET:
        analysis = Analysis.from_params(request.GET)
    else:
        analysis = None

    codes = BNFCode.objects.exclude(code__startswith="2")
    tree = make_bnf_tree(codes)
    code_to_name = make_code_to_name(codes)

    ctx = {
        "analysis": analysis,
        "code_to_name": code_to_name,
        "tree": tree,
    }
    return render(request, "build_analysis.html", ctx)


def measure(request, measure_name):
    analysis_dict = load_measure(measure_name)
    analysis_dict["org_id"] = request.GET.get("org_id")
    analysis = Analysis.from_dict(analysis_dict)

    ctx = _build_analysis_context(analysis)
    ctx["measure"] = True
    ctx["measure_title"] = analysis_dict["metadata"]["title"]
    ctx["why_it_matters"] = markdown.markdown(
        analysis_dict["metadata"]["why_it_matters"]
    )
    ctx["tags"] = analysis_dict["metadata"]["tags"]
    ctx["analysis_presentation"] = None

    return render(request, "analysis.html", ctx)


def all_measures(request):
    return render(request, "measure_list.html", {"measures": all_measure_details()})


def bnf_browser_tree(request):
    """This view renders an interactive tree for chapters 01 to 19 of the BNF hierarchy.
    Nodes include BNF codes down to the chemical substance level.  For products and
    presentations, see bnf_browser_table.

    Chapters 20 to 23 (devices rather than medicines) have a slightly different code
    structure, and so will need to be handled slightly differently.
    """

    codes = (
        BNFCode.objects.filter(level__lte=BNFCode.Level.CHEMICAL_SUBSTANCE)
        .exclude(code__startswith="2")
        .order_by("code")
    )
    ctx = {"tree": make_bnf_tree(codes)}
    return render(request, "bnf_browser_tree.html", ctx)


def bnf_browser_table(request, code):
    """This view renders a table showing all of the products and presentations belonging
    to a chemical substance.

    See docstring of make_bnf_table for a description of the structure of the table.
    """

    # Although we don't use the object found here, we want to return a 404 if the code
    # doesn't correspond to a chemical substance.
    get_object_or_404(BNFCode, code=code, level=BNFCode.Level.CHEMICAL_SUBSTANCE)
    products = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRODUCT
    ).order_by("code")
    presentations = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRESENTATION
    ).order_by("code")

    headers, rows = make_bnf_table(products, presentations)

    ctx = {"headers": headers, "rows": rows}
    return render(request, "bnf_browser_table.html", ctx)


@require_POST
def feedback_vote(request):
    sentiment = request.POST.get("sentiment")
    if sentiment not in Feedback.Sentiment.values:
        return HttpResponseBadRequest("Invalid feedback")

    feedback = Feedback.objects.create(sentiment=sentiment)
    request.session["feedback_id"] = feedback.id
    ctx = {"state": "comment", "feedback": feedback}
    return render(request, "_feedback_banner.html", ctx)


@require_POST
def feedback_comment(request):
    # prevent reuse of the same session key to update other feedback objects
    feedback_id = request.session.pop("feedback_id", None)
    if feedback_id is None:
        return HttpResponseBadRequest("Invalid feedback")

    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.comment = request.POST.get("comment", "").strip()
    feedback.save()

    ctx = {"state": "complete", "feedback": feedback}
    return render(request, "_feedback_banner.html", ctx)
