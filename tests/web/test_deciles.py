import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix
from openprescribing.web.deciles import build_deciles_chart_df


@pytest.fixture
def pdm():
    values = np.array([[i, i + 1] for i in range(21)])
    practices = [f"PRAC{i:02}" for i in range(21)]
    months = ["2025-01-01", "2025-02-01"]
    return LabelledMatrix(values, practices, months)


def test_build_chart_df(pdm):
    chart_df = build_deciles_chart_df(pdm, practice_id=None)

    expected_df = pd.DataFrame(
        [
            ["2025-01-01", "decile-0", 0.0, "blue", (2, 6)],
            ["2025-01-01", "decile-1", 2.0, "blue", (2, 6)],
            ["2025-01-01", "decile-2", 4.0, "blue", (2, 6)],
            ["2025-01-01", "decile-3", 6.0, "blue", (2, 6)],
            ["2025-01-01", "decile-4", 8.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-01-01", "decile-5", 10.0, "blue", (6, 2)],
            ["2025-01-01", "decile-6", 12.0, "blue", (2, 6)],
            ["2025-01-01", "decile-7", 14.0, "blue", (2, 6)],
            ["2025-01-01", "decile-8", 16.0, "blue", (2, 6)],
            ["2025-01-01", "decile-9", 18.0, "blue", (2, 6)],
            ["2025-01-01", "decile-10", 20.0, "blue", (2, 6)],
            ["2025-02-01", "decile-0", 1.0, "blue", (2, 6)],
            ["2025-02-01", "decile-1", 3.0, "blue", (2, 6)],
            ["2025-02-01", "decile-2", 5.0, "blue", (2, 6)],
            ["2025-02-01", "decile-3", 7.0, "blue", (2, 6)],
            ["2025-02-01", "decile-4", 9.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-02-01", "decile-5", 11.0, "blue", (6, 2)],
            ["2025-02-01", "decile-6", 13.0, "blue", (2, 6)],
            ["2025-02-01", "decile-7", 15.0, "blue", (2, 6)],
            ["2025-02-01", "decile-8", 17.0, "blue", (2, 6)],
            ["2025-02-01", "decile-9", 19.0, "blue", (2, 6)],
            ["2025-02-01", "decile-10", 21.0, "blue", (2, 6)],
        ],
        columns=["month", "line", "value", "colour", "dash"],
    )

    assert_frame_equal(chart_df, expected_df)


def test_build_chart_df_with_practice(pdm):
    chart_df = build_deciles_chart_df(pdm, practice_id="PRAC05")

    expected_df = pd.DataFrame(
        [
            ["2025-01-01", "decile-0", 0.0, "blue", (2, 6)],
            ["2025-01-01", "decile-1", 2.0, "blue", (2, 6)],
            ["2025-01-01", "decile-2", 4.0, "blue", (2, 6)],
            ["2025-01-01", "decile-3", 6.0, "blue", (2, 6)],
            ["2025-01-01", "decile-4", 8.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-01-01", "decile-5", 10.0, "blue", (6, 2)],
            ["2025-01-01", "decile-6", 12.0, "blue", (2, 6)],
            ["2025-01-01", "decile-7", 14.0, "blue", (2, 6)],
            ["2025-01-01", "decile-8", 16.0, "blue", (2, 6)],
            ["2025-01-01", "decile-9", 18.0, "blue", (2, 6)],
            ["2025-01-01", "decile-10", 20.0, "blue", (2, 6)],
            ["2025-02-01", "decile-0", 1.0, "blue", (2, 6)],
            ["2025-02-01", "decile-1", 3.0, "blue", (2, 6)],
            ["2025-02-01", "decile-2", 5.0, "blue", (2, 6)],
            ["2025-02-01", "decile-3", 7.0, "blue", (2, 6)],
            ["2025-02-01", "decile-4", 9.0, "blue", (2, 6)],
            # Note different dash style for median
            ["2025-02-01", "decile-5", 11.0, "blue", (6, 2)],
            ["2025-02-01", "decile-6", 13.0, "blue", (2, 6)],
            ["2025-02-01", "decile-7", 15.0, "blue", (2, 6)],
            ["2025-02-01", "decile-8", 17.0, "blue", (2, 6)],
            ["2025-02-01", "decile-9", 19.0, "blue", (2, 6)],
            ["2025-02-01", "decile-10", 21.0, "blue", (2, 6)],
            # Note extra rows for practice
            ["2025-01-01", "practice", 5.0, "red", (1, 0)],
            ["2025-02-01", "practice", 6.0, "red", (1, 0)],
        ],
        columns=["month", "line", "value", "colour", "dash"],
    )

    assert_frame_equal(chart_df, expected_df)
