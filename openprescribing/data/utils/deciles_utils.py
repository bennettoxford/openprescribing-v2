import pandas as pd


def _restructure_df(df):
    series = df.unstack()
    series.index.names = ["month", "line"]
    return series.reset_index(name="value")


def build_all_orgs_df(odm):
    org_codes = [org.id for org in odm.row_labels]
    dates = [str(date) for date in odm.col_labels]
    all_orgs_df = pd.DataFrame(odm.values, index=org_codes, columns=dates)
    return _restructure_df(all_orgs_df)


def build_org_df(odm, org):
    org_values = odm.get_row(org)
    org_df = pd.DataFrame({"month": odm.col_labels, "value": org_values})
    return org_df
