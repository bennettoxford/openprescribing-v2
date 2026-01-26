import dataclasses
import functools
from collections.abc import Hashable

import numpy as np
import scipy.sparse


type Label = Hashable | None
LabelGroup = tuple[Label, ...] | frozenset[Label, ...]


@dataclasses.dataclass
class LabelledMatrix:
    """
    Wrapper around a two-dimensional `np.ndarray` with labelled rows and columns

    A label can be anything you could use as a dictionary key (i.e. any hashable type).
    Strings are the obvious candidate, but dates or custom objects are perfectly
    acceptable. Labels can also be missing (i.e. None) if there's no appropriate label
    for a row or column.
    """

    values: np.ndarray
    row_labels: tuple[Label, ...]
    col_labels: tuple[Label, ...]

    def __post_init__(self):
        assert self.values.shape == (len(self.row_labels), len(self.col_labels))

    def __eq__(self, other):
        if not isinstance(other, LabelledMatrix):  # pragma: no cover
            return NotImplemented

        return (
            self.row_labels == other.row_labels
            and self.col_labels == other.col_labels
            # Treat NaNs in the same position as equal so we can compare results of
            # matrix operations which introduce NaNs (e.g. division).
            and np.array_equal(self.values, other.values, equal_nan=True)
        )

    def __mul__(self, n):
        isinstance(n, (int, float))
        return self.__class__(self.values * n, self.row_labels, self.col_labels)

    def __truediv__(self, other):
        assert self.row_labels == other.row_labels
        assert self.col_labels == other.col_labels
        # NumPy's default behaviour is for 0/0 to give np.nan and x/0 to give np.inf.
        # We always want np.nan, since we might be displaying the result on a chart.
        new_values = np.divide(self.values, other.values, where=(other.values != 0))
        new_values[other.values == 0] = np.nan
        return self.__class__(new_values, self.row_labels, self.col_labels)

    def group_rows(self, row_label_map: tuple[tuple[Label, LabelGroup], ...]):
        """
        Produce a new LabelledMatrix by mapping new output row labels to groups of input
        row labels, summing column-wise any rows in the same group.

        The mapping should be supplied as a sequence of pairs:

            new_label_1 -> (old_label_1, old_label_2, old_label_3)
            new_label_2 -> (old_label_4, old_label_5)
            new_label_3 -> (old_label_6,)
            new_label_4 -> ()
            ...

        Note a couple of things implied by this example:

         * it's possible for an output row to have only a single input in which case
           there's no summing taking place, just a relabelling of the row;

         * it's possible for an output row to have no inputs at all, in which case its
           values will be zero.

        Note also a bit of behaviour not implied by the example: if an input label
        doesn't exist in the input matrix then it's treated as having all zero values,
        rather than this being an error. It means we can ask e.g. what the total
        prescribing is for practices X, Y and Z and get the right answer even if
        practice Z hasn't prescribed at all in the timeframe and so isn't present in the
        input.

        Finally, we require the mapping to be an immutable type because we want to use
        caching and we can't use mutable values directly as cache keys.
        """
        row_grouper, new_row_labels = create_row_grouper(self.row_labels, row_label_map)
        grouped_values = row_grouper(self.values)
        return self.__class__(grouped_values, new_row_labels, self.col_labels)


# These "row groupers" are pure functions of their inputs, are not entirely trivial to
# construct, and are expected to be used repeatedly, so it makes sense to cache them
# rather than constantly rebuild them.
@functools.cache
def create_row_grouper(input_labels, label_map):
    """
    Construct a function which efficiently sums together groups of rows in a matrix

    All the number crunching here is done using a SciPy sparse matrix dot product, hence
    the efficiency. We just need to construct the appropriate sparse matrix. As with the
    `get_grouped_sum_ndarray` function, this is such a core operation to OpenPrescribing
    that it makes sense to optimise it even at the cost of some linear algebra.
    """
    input_label_index = {label: i for i, label in enumerate(input_labels)}

    output_labels = []
    output_label_groups = []
    for output_label, input_label_group in label_map:
        output_labels.append(output_label)
        output_label_groups.append(
            [
                input_label_index[label]
                for label in input_label_group
                # We filter any non-matching labels (see `group_rows()` docstring for
                # why we do this)
                if label in input_label_index
            ]
        )

    # We currently require that input rows appear in at most one output group. This is a
    # guard against accidental misuse rather than a hard limitation. If we end up
    # wanting to support summing an input row into multiple output groups then this
    # check can be removed.
    all_input_indexes = [i for group in output_label_groups for i in group]
    assert len(all_input_indexes) == len(set(all_input_indexes)), (
        "Single input row mapped to multiple output groups (see comments)"
    )

    # Build the sparse grouping matrix: for each output label index, we add a 1 for each
    # row index in the input that is mapped to that label.
    row_indices = []
    col_indices = []
    coefficients = []
    for output_row_index, input_indexes in enumerate(output_label_groups):
        row_indices.extend([output_row_index] * len(input_indexes))
        col_indices.extend(sorted(input_indexes))
        coefficients.extend([1] * len(input_indexes))

    n_input_rows = len(input_labels)
    n_output_rows = len(output_labels)

    grouping_matrix = scipy.sparse.csr_matrix(
        (coefficients, (row_indices, col_indices)), shape=(n_output_rows, n_input_rows)
    )

    # We use the matrix dot product to perform the grouping/summing, but that's an
    # implementation detail so we just return a reference to the `.dot` method as an
    # opaque "function which does the right thing here".
    row_grouper = grouping_matrix.dot

    return row_grouper, tuple(output_labels)
