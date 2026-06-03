import json
import re
from urllib.parse import urlencode

import pytest
from django.urls import reverse

from openprescribing.data.measures.measures import load_measure
from openprescribing.web.analysis_presentation import ChartType
from openprescribing.web.models import Feedback


def test_analysis(client, sample_data):
    rsp = client.get("")
    assert rsp.status_code == 200

    rsp = client.get("?ntr_bnf_codes=1001030U0")
    assert rsp.status_code == 200
    assert (
        "numerator%22%3A+%7B%22bnf_codes%22%3A+%7B%22included%22%3A+%5B%221001030U0"
        in rsp.context["prescribing_deciles_url"]
    )
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES
    assert rsp.context["org_type_label"] == "ICB"

    rsp = client.get("?ntr_bnf_codes=1001030U0&dtr_bnf_codes=1001")
    assert rsp.status_code == 200
    assert (
        "denominator%22%3A+%7B%22bnf_codes%22%3A+%7B%22included%22%3A+%5B%221001"
        in rsp.context["prescribing_deciles_url"]
    )

    rsp = client.get("?ntr_bnf_codes=1001030U0AAABAB,1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        "numerator%22%3A+%7B%22bnf_codes%22%3A+%7B%22included%22%3A+%5B%221001030U0AAABAB%22%2C+%221001030U0AAABAB"
        in rsp.context["prescribing_deciles_url"]
    )

    rsp = client.get(
        "?ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB"
    )
    assert rsp.status_code == 200
    assert (
        "numerator%22%3A+%7B%22bnf_codes%22%3A+%7B%22included%22%3A+%5B%221001030U0AA%22%5D%2C+%22excluded%22%3A+%5B%221001030U0AAABAB"
        in rsp.context["prescribing_deciles_url"]
    )

    rsp = client.get(
        "?ntr_bnf_codes=1001030U0AA&ntr_bnf_codes_excluded=1001030U0AAABAB&org_id=PRA00"
    )
    assert rsp.status_code == 200
    assert "org_id%22%3A+%22PRA00" in rsp.context["prescribing_deciles_url"]
    assert rsp.context["org_type_label"] == "Practice"

    rsp = client.get("?ntr_bnf_codes=1001030U0&chart_type=all-orgs-line")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.ALL_ORGS_LINE
    assert re.search(r'id="all-orgs-line"[^>]*checked', rsp.content.decode())

    rsp = client.get("?ntr_bnf_codes=1001030U0&chart_type=invalid")
    assert rsp.status_code == 200
    assert rsp.context["analysis_presentation"].chart_type == ChartType.DECILES


def test_analysis_build(client, sample_data):
    rsp = client.get("/analysis/build/")
    assert rsp.status_code == 200

    rsp = client.get("/analysis/build/?ntr_bnf_codes=1001030U0")
    assert rsp.status_code == 200


def test_bnf_tree(client, bnf_codes):
    rsp = client.get("/bnf/")
    assert rsp.status_code == 200


def test_bnf_table_with_generic_products(client, bnf_codes):
    rsp = client.get("/bnf/1001030U0/")
    assert rsp.status_code == 200


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


def test_analysis_download(client, sample_data, tmp_path, settings):
    analysis_dict = {
        "output": {"numerator": "items", "denominator": "list_size"},
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["01"],
                    },
                    "ingredient_ids": [1],
                },
            }
        ],
    }
    analysis_param = urlencode({"analysis": json.dumps(analysis_dict)})

    rsp = client.get(f"/analysis/download/?{analysis_param}")
    assert rsp.status_code == 200

    (tmp_path / "test-measure.yaml").write_bytes(rsp.content)
    settings.MEASURE_DEFINITIONS_PATH = tmp_path

    expected_analysis_dict = {
        **analysis_dict,
        "metadata": {
            "tags": [
                "builder",
            ],
            "title": "Analysis created by analysis builder",
            "why_it_matters": "TODO",
        },
    }
    received_analysis_dict = load_measure("test-measure")
    assert received_analysis_dict == expected_analysis_dict
