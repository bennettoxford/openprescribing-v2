import json
from urllib.parse import urlencode


def analysis_querystring(numerator, denominator=None, **extra):
    # Build an analysis querystring with the BNF query (or queries) serialised as a
    # single JSON `analysis` param, plus any extra flat params (eg `org_id`,
    # `chart_type`).
    query = {"numerator": numerator}
    if denominator is None:
        options = {"type": "prescribing_vs_list_size", "output_value": "items"}
    else:
        query["denominator"] = denominator
        options = {"type": "prescribing_vs_prescribing", "output_value": "items"}
    analysis_dict = {"options": options, "queries": [query]}
    return urlencode({"analysis": json.dumps(analysis_dict), **extra})
