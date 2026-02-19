import numpy as np
import pandas as pd


def _restructure_df(df):
    series = df.unstack()
    series.index.names = ["month", "line"]
    return series.reset_index(name="value")


def build_deciles_df(odm):
    centiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    # rows are centiles, columns are dates
    cdm = np.nanpercentile(odm.values, centiles, axis=0)
    deciles_df = pd.DataFrame(cdm, columns=odm.col_labels)
    deciles_df = _restructure_df(deciles_df)
    deciles_df["line"] = deciles_df["line"].apply(lambda n: f"p{centiles[n]:02}")
    return deciles_df


def build_all_orgs_df(odm):
    org_codes = [org.id for org in odm.row_labels]
    dates = [str(date) for date in odm.col_labels]
    all_orgs_df = pd.DataFrame(odm.values, index=org_codes, columns=dates)
    return _restructure_df(all_orgs_df)


def build_org_df(odm, org):
    org_ix = odm.row_labels.index(org)
    org_values = odm.values[org_ix]
    org_df = pd.DataFrame({"month": odm.col_labels, "value": org_values})
    return org_df
