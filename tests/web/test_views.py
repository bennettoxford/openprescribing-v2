import re

import pytest

from openprescribing.web.analysis_presentation import ChartType
from openprescribing.web.models import Feedback


@pytest.mark.django_db(databases=["data"])
def test_query(client, sample_data):
    rsp = client.get("")
    assert rsp.status_code == 200

    rsp = client.get("?ntr_codes=1001030U0")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0&ntr_product_type=all"
    )
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES
    assert re.search(
        r'id="prescribing-query-org-id"[^>]*name="org_id"[^>]*disabled',
        rsp.content.decode(),
    )

    rsp = client.get("?ntr_codes=1001030U0&dtr_codes=1001")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0&ntr_product_type=all&dtr_codes=1001&dtr_product_type=all"
    )

    rsp = client.get("?ntr_codes=1001030U0AAABAB,1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0AAABAB,1001030U0AAABAB&ntr_product_type=all"
    )

    rsp = client.get("?ntr_codes=1001030U0AA,-1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0AA,-1001030U0AAABAB&ntr_product_type=all"
    )

    rsp = client.get("?ntr_codes=1001030U0AA,-1001030U0AAABAB&org_id=PRA00")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_deciles_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0AA,-1001030U0AAABAB&ntr_product_type=all&org_id=PRA00"
    )
    assert re.search(
        r'id="prescribing-query-org-id"[^>]*name="org_id"[^>]*value="PRA00"',
        rsp.content.decode(),
    )

    rsp = client.get("?ntr_codes=1001030U0&chart_type=all-orgs-line")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.ALL_ORGS_LINE
    assert re.search(r'id="all_orgs_line_chart"[^>]*checked', rsp.content.decode())

    rsp = client.get("?ntr_codes=1001030U0&chart_type=invalid")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES


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
    rsp = client.post("/feedback/vote/", {"sentiment": Feedback.Sentiment.THUMBS_UP})

    assert rsp.status_code == 200
    assert rsp.context["state"] == "detail"
    feedback = Feedback.objects.get()
    assert feedback.sentiment == Feedback.Sentiment.THUMBS_UP
    assert b"feedback_id" in rsp.content


def test_feedback_vote_invalid_sentiment(client):
    rsp = client.post("/feedback/vote/", {"sentiment": "flat"})

    assert rsp.status_code == 400


@pytest.mark.django_db
def test_feedback_detail(client):
    feedback = Feedback.objects.create(sentiment=Feedback.Sentiment.THUMBS_DOWN)

    rsp = client.post(
        "/feedback/detail/",
        {"feedback_id": feedback.id, "comment": "This is additional detail."},
    )

    feedback.refresh_from_db()

    assert rsp.status_code == 200
    assert feedback.comment == "This is additional detail."
