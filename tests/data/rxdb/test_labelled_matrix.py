import numpy as np
import pytest

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix


def test_eq():
    values = np.array([[1.0, np.nan], [2.0, 3.0]])
    matrix = LabelledMatrix(values, ("A", "B"), (1, 2))

    assert matrix == LabelledMatrix(values, ("A", "B"), (1, 2))

    # Different row labels
    assert matrix != LabelledMatrix(values, ("A", "C"), (1, 2))

    # Different column  labels
    assert matrix != LabelledMatrix(values, ("A", "B"), (1, 3))

    # Different values
    assert matrix != LabelledMatrix(
        np.array([[1.0, np.nan], [2.0, 4.0]]), ("A", "B"), (1, 2)
    )


def test_mul():
    matrix = LabelledMatrix(np.array([[1, np.nan], [2, 3]]), ("A", "B"), (1, 2))
    assert matrix * 10 == LabelledMatrix(
        np.array([[10, np.nan], [20, 30]]), ("A", "B"), (1, 2)
    )


def test_truediv():
    ntr = LabelledMatrix(np.array([[0, 1], [0, 1]]), ("A", "B"), (1, 2))
    dtr = LabelledMatrix(np.array([[0, 0], [1, 1]]), ("A", "B"), (1, 2))
    assert ntr / dtr == LabelledMatrix(
        np.array([[np.nan, np.nan], [0, 1]]), ("A", "B"), (1, 2)
    )


def test_repr():
    matrix = LabelledMatrix(
        np.array([range(100), range(100)]),
        ("r1", "r2"),
        tuple(f"c{x}" for x in range(100)),
    )
    assert (
        repr(matrix)
        == "LabelledMatrix(values=array([[ 0, ... 97, 98, 99]]), row_labels=('r1', 'r2'), col_labels=('c0', 'c1', 'c2', 'c3', 'c4', 'c5', ...))"
    )


def test_group_rows_by_label():
    matrix = LabelledMatrix(
        col_labels=(1, 2, 3),
        row_labels=("A", "B", "C", "D"),
        values=np.array(
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


def test_get_row():
    matrix = LabelledMatrix(np.array([[1.0, 2.0], [3.0, 4.0]]), ("A", "B"), (1, 2))
    assert np.array_equal(matrix.get_row("A"), np.array([1.0, 2.0]))
