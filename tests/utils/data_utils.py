import datetime

from openprescribing.data.models import BNFCode, Org, OrgRelation


def generate_test_data(rxdb, bnf_codes):
    """Generate and ingest list size and prescribing data for the given presentation BNF
    codes.

    Generates three months (Jan-Mar 2025) of list size data, and prescribing data for
    each of `bnf_codes`, across four practices in two ICBs.  This should be just about
    rich enough for the tests of the website and API.

    Returns a dict of the generated data so callers can compute expected values from it.
    """
    for code in bnf_codes:
        BNFCode.objects.get_or_create(
            code=code,
            defaults={"name": code, "level": BNFCode.Level.PRESENTATION},
        )

    list_size_data = []
    prescribing_data = []

    for icb_ix in range(2):
        icb = Org.objects.create(
            id=f"ICB{icb_ix:02}",
            name=f"ICB {icb_ix}",
            org_type=Org.OrgType.ICB,
        )
        for pra_ix in range(2):
            pra = Org.objects.create(
                id=f"PRA{icb_ix}{pra_ix}",
                name=f"Practice {icb_ix}{pra_ix}",
                org_type=Org.OrgType.PRACTICE,
            )
            OrgRelation.objects.create(child=pra, parent=icb)
            for month in (1, 2, 3):
                date = datetime.date(2025, month, 1)
                list_size_data.append(
                    {
                        "date": date,
                        "practice_code": pra.id,
                        "total": 1000 + 100 * icb_ix + 10 * pra_ix + month,
                    }
                )
                for bnf_ix, bnf_code in enumerate(bnf_codes):
                    prescribing_data.append(
                        {
                            "date": date,
                            "bnf_code": bnf_code,
                            "practice_code": pra.id,
                            "items": 8 * bnf_ix + 4 * icb_ix + 2 * pra_ix + month,
                        },
                    )

    rxdb.ingest(
        list_size_data=list_size_data,
        prescribing_data=prescribing_data,
    )

    return {"list_size_data": list_size_data, "prescribing_data": prescribing_data}
