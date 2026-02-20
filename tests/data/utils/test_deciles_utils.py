import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openprescribing.data.models import Org
from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix
from openprescribing.data.utils.deciles_utils import (
    build_all_orgs_df,
    build_org_df,
)


@pytest.fixture
def pdm_small():
    values = np.array([[i, i + 1] for i in range(5)])
    practices = [
        Org.objects.create(
            id=f"PRAC{i:02}", name=f"Practice {i}", org_type=Org.OrgType.PRACTICE
        )
        for i in range(5)
    ]
    months = ["2025-01-01", "2025-02-01"]
    return LabelledMatrix(values, practices, months)


@pytest.mark.django_db(databases=["data"])
def test_build_all_orgs_df(pdm_small):
    chart_df = build_all_orgs_df(pdm_small)

    expected_df = pd.DataFrame(
        [
            ["2025-01-01", "PRAC00", 0],
            ["2025-01-01", "PRAC01", 1],
            ["2025-01-01", "PRAC02", 2],
            ["2025-01-01", "PRAC03", 3],
            ["2025-01-01", "PRAC04", 4],
            ["2025-02-01", "PRAC00", 1],
            ["2025-02-01", "PRAC01", 2],
            ["2025-02-01", "PRAC02", 3],
            ["2025-02-01", "PRAC03", 4],
            ["2025-02-01", "PRAC04", 5],
        ],
        columns=["month", "line", "value"],
    )

    assert_frame_equal(chart_df, expected_df)


@pytest.mark.django_db(databases=["data"])
def test_build_org_df(pdm):
    chart_df = build_org_df(pdm, org=Org.objects.get(id="PRAC05"))

    expected_df = pd.DataFrame(
        [["2025-01-01", 5], ["2025-02-01", 6]],
        columns=["month", "value"],
    )

    assert_frame_equal(chart_df, expected_df)
