import json
from urllib.parse import urlencode

import markdown
import yaml
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from openprescribing.data.analysis import Analysis
from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery
from openprescribing.data.measures import all_measure_details, load_measure
from openprescribing.data.models import BNFCode, Org

from .analysis_presentation import AnalysisPresentation
from .charts import build_medications_chart_spec, build_org_chart_spec
from .models import Feedback
from .presenters import (
    make_bnf_table,
    make_bnf_tree,
    make_ntr_dtr_intersection_table,
    make_orgs,
)


def _build_analysis_context(analysis, medications_order):
    build_analysis_url = reverse("build-analysis")
    download_analysis_url = reverse("download-analysis")
    deciles_api_url = None
    all_orgs_api_url = None
    medications_api_url = None
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
            assert isinstance(analysis.dtr_query, ListSizeQuery)
            ntr_dtr_intersection_table = make_ntr_dtr_intersection_table(
                analysis.ntr_query, None
            )

        url_parameters_json = urlencode({"analysis": json.dumps(analysis.to_dict())})
        build_analysis_url = f"{reverse('build-analysis')}?{url_parameters_json}"
        download_analysis_url = f"{reverse('download-analysis')}?{url_parameters_json}"
        deciles_api_url = f"{reverse('api_prescribing_deciles')}?{url_parameters_json}"
        all_orgs_api_url = (
            f"{reverse('api_prescribing_all_orgs')}?{url_parameters_json}"
        )
        medications_api_url = (
            f"{reverse('api_prescribing_medications')}?{url_parameters_json}"
        )

    orgs = make_orgs()

    org_type = Org.OrgType(org.org_type) if org is not None else Org.OrgType.ICB

    ctx = {
        "analysis": analysis,
        "ntr_dtr_intersection_table": ntr_dtr_intersection_table,
        "org": org,
        "orgs": orgs,
        "org_types": Org.OrgType.choices,
        "org_type_label": org_type.label,
        "build_analysis_url": build_analysis_url,
        "download_analysis_url": download_analysis_url,
        "prescribing_urls": {
            "deciles": deciles_api_url,
            "all_orgs": all_orgs_api_url,
            "medications": medications_api_url,
        },
        "chart_specs": {
            "org": build_org_chart_spec(analysis),
            "medications": build_medications_chart_spec(analysis, **medications_order),
        },
    }

    return ctx


def analysis(request):
    analysis_presentation = AnalysisPresentation.from_params(request.GET)

    analysis_json = request.GET.get("analysis")
    if analysis_json:
        analysis_dict = json.loads(analysis_json)
        analysis_dict["org_id"] = request.GET.get("org_id")
        analysis = Analysis.from_dict(analysis_dict)
    else:
        analysis = None

    ctx = _build_analysis_context(analysis, _medications_order(request))
    ctx["measure"] = False
    ctx["analysis_presentation"] = analysis_presentation

    return render(request, "analysis.html", ctx)


def _medications_order(request):
    """Pull the "by medication" chart ordering from the query string, e.g.
    ?largest=bottom&other=top.  Unknown values fall back to the chart's defaults.

    Intended to be a temporary solution to get feedback.
    """
    order = {}
    for key in ("largest", "other"):
        if key in request.GET:  # pragma: no cover
            order[key] = request.GET[key]
    return order


def build_analysis(request):
    panels = [
        {"prefix": "ntr", "label": "Numerator"},
        {"prefix": "dtr", "label": "Denominator"},
    ]
    return render(request, "build_analysis.html", {"panels": panels})


def download_analysis(request):

    analysis = Analysis.from_dict(json.loads(request.GET["analysis"]))
    analysis_dict = analysis.to_dict()

    analysis_dict["metadata"] = {
        "title": "Analysis created by analysis builder",
        "why_it_matters": "TODO",
        "tags": ["builder"],
    }

    response = HttpResponse(yaml.dump(analysis_dict))
    response["Content-Disposition"] = 'attachment; filename="analysis.yaml"'

    return response


def measure(request, measure_name):
    analysis_dict = load_measure(measure_name)
    analysis_dict["org_id"] = request.GET.get("org_id")
    analysis = Analysis.from_dict(analysis_dict)

    try:
        analysis.validate()
    except ValueError as e:
        return render(
            request, "analysis.html", {"measure": True, "validation_error": str(e)}
        )

    ctx = _build_analysis_context(analysis, _medications_order(request))
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
