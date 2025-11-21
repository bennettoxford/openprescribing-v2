import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openprescribing.data.models import Org
from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix
from openprescribing.web.deciles import build_deciles_chart_df


@pytest.fixture
def pdm():
    values = np.array([[i, i + 1] for i in range(21)])
    practices = [
        Org.objects.create(
            id=f"PRAC{i:02}", name=f"Practice {i}", org_type=Org.OrgType.PRACTICE
        )
        for i in range(21)
    ]
    months = ["2025-01-01", "2025-02-01"]
    return LabelledMatrix(values, practices, months)


@pytest.mark.django_db(databases=["data"])
def test_build_chart_df(pdm):
    chart_df = build_deciles_chart_df(pdm, practice=None)

    expected_df = pd.DataFrame(
        [
            ["2025-01-01", "p10", 2.0, "blue", (2, 6)],
            ["2025-01-01", "p20", 4.0, "blue", (2, 6)],
            ["2025-01-01", "p30", 6.0, "blue", (2, 6)],
            ["2025-01-01", "p40", 8.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-01-01", "p50", 10.0, "blue", (6, 2)],
            ["2025-01-01", "p60", 12.0, "blue", (2, 6)],
            ["2025-01-01", "p70", 14.0, "blue", (2, 6)],
            ["2025-01-01", "p80", 16.0, "blue", (2, 6)],
            ["2025-01-01", "p90", 18.0, "blue", (2, 6)],
            ["2025-02-01", "p10", 3.0, "blue", (2, 6)],
            ["2025-02-01", "p20", 5.0, "blue", (2, 6)],
            ["2025-02-01", "p30", 7.0, "blue", (2, 6)],
            ["2025-02-01", "p40", 9.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-02-01", "p50", 11.0, "blue", (6, 2)],
            ["2025-02-01", "p60", 13.0, "blue", (2, 6)],
            ["2025-02-01", "p70", 15.0, "blue", (2, 6)],
            ["2025-02-01", "p80", 17.0, "blue", (2, 6)],
            ["2025-02-01", "p90", 19.0, "blue", (2, 6)],
        ],
        columns=["month", "line", "value", "colour", "dash"],
    )

    assert_frame_equal(chart_df, expected_df)


@pytest.mark.django_db(databases=["data"])
def test_build_chart_df_with_practice(pdm):
    chart_df = build_deciles_chart_df(pdm, practice=Org.objects.get(id="PRAC05"))

    expected_df = pd.DataFrame(
        [
            ["2025-01-01", "p10", 2.0, "blue", (2, 6)],
            ["2025-01-01", "p20", 4.0, "blue", (2, 6)],
            ["2025-01-01", "p30", 6.0, "blue", (2, 6)],
            ["2025-01-01", "p40", 8.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-01-01", "p50", 10.0, "blue", (6, 2)],
            ["2025-01-01", "p60", 12.0, "blue", (2, 6)],
            ["2025-01-01", "p70", 14.0, "blue", (2, 6)],
            ["2025-01-01", "p80", 16.0, "blue", (2, 6)],
            ["2025-01-01", "p90", 18.0, "blue", (2, 6)],
            ["2025-02-01", "p10", 3.0, "blue", (2, 6)],
            ["2025-02-01", "p20", 5.0, "blue", (2, 6)],
            ["2025-02-01", "p30", 7.0, "blue", (2, 6)],
            ["2025-02-01", "p40", 9.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-02-01", "p50", 11.0, "blue", (6, 2)],
            ["2025-02-01", "p60", 13.0, "blue", (2, 6)],
            ["2025-02-01", "p70", 15.0, "blue", (2, 6)],
            ["2025-02-01", "p80", 17.0, "blue", (2, 6)],
            ["2025-02-01", "p90", 19.0, "blue", (2, 6)],
            # Note extra rows for practice
            ["2025-01-01", "practice", 5.0, "red", (1, 0)],
            ["2025-02-01", "practice", 6.0, "red", (1, 0)],
        ],
        columns=["month", "line", "value", "colour", "dash"],
    )

    assert_frame_equal(chart_df, expected_df)
