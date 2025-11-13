import dataclasses
from collections.abc import Hashable

import numpy


type Label = Hashable | None


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
