import dataclasses
import functools
from collections import defaultdict
from collections.abc import Hashable

import numpy
import scipy.sparse


type Label = Hashable | None
LabelPair = tuple[Label, Label]


@dataclasses.dataclass
class LabelledMatrix:
    """
    Wrapper around a two-dimensional `numpy.ndarray` with labelled rows and columns

    A label can be anything you could use as a dictionary key (i.e. any hashable type).
    Strings are the obvious candidate, but dates or custom objects are perfectly
    acceptable. Labels can also be missing (i.e. None) if there's no appropriate label
    for a row or column.
    """

    values: numpy.ndarray
    row_labels: tuple[Label, ...]
    col_labels: tuple[Label, ...]

    def __post_init__(self):
        assert self.values.shape == (len(self.row_labels), len(self.col_labels))

    def group_rows_by_label(self, row_label_map: tuple[LabelPair, ...]):
        """
        Produce a new LabelledMatrix by mapping the existing set of rows to a new set
        using the supplied mapping, grouping together (i.e. summing column-wise) any
        rows which are mapped to the same output label.

        The mapping should be supplied as a sequence of pairs:

            old_label_1 -> new_label_1
            old_label_2 -> new_label_1
            old_label_3 -> new_label_2
            old_label_4 -> new_label_2
            ...

        Note that it's possible to just select a subset of rows without doing any
        grouping simply by ensuring that each input row maps to at most one output row:

            old_label_1 -> new_label_1
            old_label_4- > new_label_2
            old_label_9- > new_label_3
            ...

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
    Construct a function which can efficiently sum together arbitrary groups of rows in a matrix

    All the number crunching here is done using a SciPy sparse matrix dot product, hence
    the efficiency. We just need to construct the appropriate sparse matrix. As with the
    `get_grouped_sum_ndarray` function, this is such a core operation to OpenPrescribing
    that it makes sense to optimise it even at the cost of some linear algebra.
    """
    input_label_index = {label: i for i, label in enumerate(input_labels)}

    # Build a mapping from output labels to the list of input row indexes which are
    # mapped to that label
    output_labels = defaultdict(list)
    for input_label, output_label in label_map:
        input_indexes = output_labels[output_label]
        try:
            input_index = input_label_index[input_label]
        except KeyError:
            # It's convenient for our purposes if missing input row labels don't throw
            # errors but are treated as, effectively, zero-valued rows. It means we ask
            # e.g. what the total prescribing is for practices X, Y and Z and get the
            # right answer even if practice Z hasn't prescribed at all and isn't present
            # in the input.
            continue
        input_indexes.append(input_index)

    # Build the sparse grouping matrix: for each output label index, we add a 1 for each
    # row index in the input that is mapped to that label.
    row_indices = []
    col_indices = []
    coefficients = []
    for output_row_index, input_indexes in enumerate(output_labels.values()):
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
