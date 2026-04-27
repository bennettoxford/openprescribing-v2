import re

import pytest
from django.urls import reverse

from openprescribing.web.analysis_presentation import ChartType
from openprescribing.web.models import Feedback


@pytest.mark.django_db(databases=["data"])
def test_analysis(client, sample_data):
    rsp = client.get("")
    assert rsp.status_code == 200

    rsp = client.get("?ntr_bnf_codes=1001030U0")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_product_type=all&ntr_bnf_codes=1001030U0"
    )
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES

    rsp = client.get("?ntr_bnf_codes=1001030U0&dtr_bnf_codes=1001")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_product_type=all&ntr_bnf_codes=1001030U0&dtr_product_type=all&dtr_bnf_codes=1001"
    )

    rsp = client.get("?ntr_bnf_codes=1001030U0AAABAB,1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_product_type=all&ntr_bnf_codes=1001030U0AAABAB,1001030U0AAABAB"
    )

    rsp = client.get(
        "?ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB"
    )
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_product_type=all&ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB"
    )

    rsp = client.get(
        "?ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB&org_id=PRA00"
    )
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_product_type=all&ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB&org_id=PRA00"
    )

    rsp = client.get("?ntr_bnf_codes=1001030U0&chart_type=all-orgs-line")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.ALL_ORGS_LINE
    assert re.search(r'id="all_orgs_line_chart"[^>]*checked', rsp.content.decode())

    rsp = client.get("?ntr_bnf_codes=1001030U0&chart_type=invalid")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES


@pytest.mark.django_db(databases=["data"])
def test_analysis_build(client, sample_data):
    rsp = client.get("/analysis/build/")
    assert rsp.status_code == 200

    rsp = client.get("/analysis/build/?ntr_bnf_codes=1001030U0")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_bnf_tree(client, bnf_codes):
    rsp = client.get("/bnf/")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_bnf_table_with_generic_products(client, bnf_codes):
    rsp = client.get("/bnf/1001030U0/")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_bnf_table_with_no_generic_products(client, bnf_codes):
    rsp = client.get("/bnf/0601060D0/")
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_feedback_vote(client):
    rsp = client.post(
        reverse("feedback_vote"), {"sentiment": Feedback.Sentiment.THUMBS_UP}
    )

    assert rsp.status_code == 200
    assert rsp.context["state"] == "comment"
    feedback = Feedback.objects.get()
    assert feedback.sentiment == Feedback.Sentiment.THUMBS_UP


def test_feedback_vote_rejects_invalid_sentiment(client):
    rsp = client.post(reverse("feedback_vote"), {"sentiment": "bored"})

    assert rsp.status_code == 400


@pytest.mark.django_db
def test_feedback_comment(client):
    client.post(reverse("feedback_vote"), {"sentiment": Feedback.Sentiment.THUMBS_DOWN})

    rsp = client.post(reverse("feedback_comment"), {"comment": "Additional detail"})

    assert rsp.status_code == 200
    feedback = Feedback.objects.get()
    assert feedback.comment == "Additional detail"


@pytest.mark.django_db
def test_feedback_comment_rejects_missing_session(client):
    feedback = Feedback.objects.create(sentiment=Feedback.Sentiment.THUMBS_UP)

    rsp = client.post(reverse("feedback_comment"), {"comment": "Missing session"})

    assert rsp.status_code == 400
    feedback.refresh_from_db()
    assert feedback.comment == ""


@pytest.mark.django_db(databases=["data"])
def test_measure(client, sample_data, tmp_path, settings):
    test_yaml = """
metadata:
  title: test title
  why_it_matters: This is a demo measure
  tags:
    - demo
output:
  numerator: items
  denominator: list_size
queries:
  - numerator:
      bnf_codes:
        included:
          - "0501013"

"""
    (tmp_path / "test-measure.yaml").write_text(test_yaml)
    settings.MEASURE_DEFINITIONS_PATH = tmp_path

    rsp = client.get("/measures/")
    assert rsp.status_code == 200

    rsp = client.get("/measures/test-measure/")
    assert rsp.status_code == 200
