import numpy as np
import pandas as pd


def build_deciles_df(odm):
    centiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    deciles_arr = np.nanpercentile(odm.values, centiles, axis=0)
    deciles_df = pd.DataFrame(deciles_arr, columns=odm.col_labels)
    series = deciles_df.unstack()
    series.index.names = ["month", "line"]
    deciles_df = series.reset_index(name="value")
    deciles_df["line"] = deciles_df["line"].apply(lambda n: f"p{centiles[n]:02}")
    return deciles_df


def build_org_df(odm, org):
    org_ix = odm.row_labels.index(org)
    org_values = odm.values[org_ix]
    org_df = pd.DataFrame({"month": odm.col_labels, "value": org_values})
    return org_df
