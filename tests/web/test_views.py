import json

import pytest

from openprescribing.data.models import BNFCode


@pytest.mark.django_db(databases=["data"])
def test_index(client):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)

    rsp = client.get("/?code=0601023AW")
    assert rsp.status_code == 200

    spec = json.loads(rsp.context["chart_spec"])
    assert spec["mark"]["type"] == "line"
