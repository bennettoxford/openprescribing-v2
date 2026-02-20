import numpy as np

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix


def get_centiles(labelled_matrix):
    centiles = (10, 20, 30, 40, 50, 60, 70, 80, 90)
    values = np.nanpercentile(labelled_matrix.values, centiles, axis=0)
    return LabelledMatrix(values, centiles, labelled_matrix.col_labels)
