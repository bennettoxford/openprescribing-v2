import numpy
import pytest
from numpy.testing import assert_array_equal

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix


def test_div():
    ntr = LabelledMatrix(numpy.array([[0, 1], [0, 1]]), ("A", "B"), (1, 2))
    dtr = LabelledMatrix(numpy.array([[0, 0], [1, 1]]), ("A", "B"), (1, 2))
    ratio = ntr / dtr
    assert ratio.row_labels == ("A", "B")
    assert ratio.col_labels == (1, 2)
    assert_array_equal(ratio.values, numpy.array([[numpy.nan, numpy.nan], [0, 1]]))


def test_group_rows_by_label():
    matrix = LabelledMatrix(
        col_labels=(1, 2, 3),
        row_labels=("A", "B", "C", "D"),
        values=numpy.array(
            [
                [0, 1, 2],
                [3, 4, 5],
                [6, 7, 8],
                [9, 0, 1],
            ],
        ),
    )

    # Split into two groups and sum within each group
    summed_1 = matrix.group_rows(
        (
            ("one", ("A", "C")),
            ("two", ("B", "D")),
        )
    )

    assert summed_1.col_labels == matrix.col_labels
    assert summed_1.row_labels == ("one", "two")
    assert summed_1.values.tolist() == [
        [6, 8, 10],
        [12, 4, 6],
    ]

    # Select a subset of rows, re-ordered and re-labelled but with no summing
    summed_2 = matrix.group_rows(
        (
            ("H", ("C",)),
            ("I", ("B",)),
            ("J", ("D",)),
        )
    )

    assert summed_2.col_labels == matrix.col_labels
    assert summed_2.row_labels == ("H", "I", "J")
    assert summed_2.values.tolist() == [
        [6, 7, 8],
        [3, 4, 5],
        [9, 0, 1],
    ]

    # Missing input rows are treated as empty
    summed_3 = matrix.group_rows(
        (
            ("X", ("A", "B")),
            ("Y", ("D", "_")),
            ("Z", ("*",)),
        )
    )

    assert summed_3.col_labels == matrix.col_labels
    assert summed_3.row_labels == ("X", "Y", "Z")
    assert summed_3.values.tolist() == [
        [3, 5, 7],
        [9, 0, 1],
        [0, 0, 0],
    ]

    # Non-unique mappings are rejected
    with pytest.raises(AssertionError, match="input row mapped to multiple"):
        matrix.group_rows(
            (
                ("X", ("A", "B", "C")),
                ("Y", ("A", "C")),
            )
        )
