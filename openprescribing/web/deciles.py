import numpy as np
import pandas as pd


def build_deciles_chart_df(odm, org):
    """Return a DataFrame that can be passed to Altair to display a deciles chart.

    The chart will show blue dotted lines indicating the value at each decile for each
    month in the given PDM.  The median value will be shown in a heavier dashed line.

    Additionally, if org is not None, the chart will show a solid red line for that
    org's values.

    The DataFrame will have one row per point on the chart, with the following columns:

        * month
        * line
        * value
        * colour
        * dash

    Points are grouped by line, which will be "decile-{n}" or "org".

    Dashes are specified as (on, off) pairs:

        * (2, 6) gives a dotted line
        * (6, 2) gives a dashed line
        * (1, 0) gives a continuous line
    """
    deciles_df = _build_deciles_df(odm)

    if org is None:
        return deciles_df
    else:
        org_df = _build_org_df(odm, org)
        return pd.concat([deciles_df, org_df], ignore_index=True)


def _build_deciles_df(odm):
    centiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    deciles_arr = np.nanpercentile(odm.values, centiles, axis=0)
    deciles_df = pd.DataFrame(deciles_arr, columns=odm.col_labels)
    series = deciles_df.unstack()
    series.index.names = ["month", "line"]
    deciles_df = series.reset_index(name="value")
    deciles_df["line"] = deciles_df["line"].apply(lambda n: f"p{centiles[n]:02}")
    deciles_df["colour"] = "blue"
    deciles_df["dash"] = deciles_df["line"].apply(
        lambda line: (6, 2) if line == "p50" else (2, 6)
    )
    return deciles_df


def _build_org_df(odm, org):
    org_ix = odm.row_labels.index(org)
    org_values = odm.values[org_ix]
    org_df = pd.DataFrame(
        {
            "month": odm.col_labels,
            "line": "org",
            "value": org_values,
            "colour": "red",
            "dash": [(1, 0)] * len(org_values),
        }
    )
    return org_df
