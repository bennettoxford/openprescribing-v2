import datetime

import pytest

from openprescribing.data.models import BNFCode, Org, OrgRelation


@pytest.fixture
def sample_data(rxdb):
    """This fixture generates three months (Jan-Mar 2025) of list size and prescribing
    data (for generic and branded methotrexate) for four practices in two ICBs.

    This data should be just about rich enough for the tests of the website and API.
    """

    for level, code, name in [
        [1, "10", "Musculoskeletal and Joint Diseases"],
        [2, "1001", "Drugs used in rheumatic diseases and gout"],
        [3, "100103", "Rheumatic disease suppressant drugs"],
        [4, "1001030", "Rheumatic disease suppressant drugs"],
        [5, "1001030U0", "Methotrexate"],
        [6, "1001030U0AA", "Methotrexate (Rheumatism)"],
        [7, "1001030U0AAABAB", "Methotrexate 2.5mg tablets"],
        [7, "1001030U0AAACAC", "Methotrexate 10mg tablets"],
        [6, "1001030U0BD", "Maxtrex (Rheumatism)"],
        [7, "1001030U0BDAAAB", "Maxtrex 2.5mg tablets"],
        [7, "1001030U0BDABAC", "Maxtrex 10mg tablets"],
    ]:
        BNFCode.objects.create(code=code, name=name, level=level)

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
                for bnf_ix, bnf_code in enumerate(
                    [
                        "1001030U0AAABAB",
                        "1001030U0AAACAC",
                        "1001030U0BDAAAB",
                        "1001030U0BDABAC",
                    ]
                ):
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
