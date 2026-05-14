import json

import pytest

from openprescribing.data.ingestors import ncso_concessions
from openprescribing.data.models.ncso_concessions import NCSOConcessions


@pytest.mark.django_db(databases=["data"])
def test_ncso_concessions_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"

    data = [
        {
            "model": "frontend.ncsoconcession",
            "pk": 1,
            "fields": {
                "date": "2018-02-01",
                "vmpp": 993111000001102,
                "drug": "Perindopril erbumine 2mg tablets",
                "pack_size": "30",
                "price_pence": 500,
            },
        },
    ]

    ncso_concessions_file = (
        settings.DOWNLOAD_DIR / "ncso_concessions" / "ncso_concessions_2026-04-01.json"
    )
    ncso_concessions_file.parent.mkdir(parents=True, exist_ok=True)
    ncso_concessions_file.touch()

    with open(ncso_concessions_file, "w") as f:
        json.dump(data, f)

    ncso_concessions.ingest()

    results = [
        (
            str(concession.date),
            concession.vmpp,
            concession.price_pence,
        )
        for concession in NCSOConcessions.objects.all()
    ]
    assert results == [
        (
            "2018-02-01",
            993111000001102,
            500,
        ),
    ]

    # Attempting to re-ingest the same named file should do nothing. As a simple check for
    # this we empty the file contents and re-ingest. If the code does attempt to load it
    # then this will fail loudly.
    ncso_concessions_file.write_text("")
    ncso_concessions.ingest()
