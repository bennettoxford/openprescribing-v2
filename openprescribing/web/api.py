import math

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse as DjangoJsonResponse

from openprescribing.data.analysis import Analysis
from openprescribing.data.models import Org
from openprescribing.data.rxdb import get_centiles


def _get_org(analysis):
    org_id = analysis.org_id

    if org_id is not None:
        return Org.objects.get(id=org_id)
    else:
        return None


def _get_org_records(odm, org):
    if org is not None:
        org_records = [
            {"month": month, "value": value}
            for month, value in zip(odm.col_labels, odm.get_row(org))
        ]
        # The organisation-date matrix (odm) can contain NaNs. NaNs are ignored when
        # deciles are computed, and so are not present in deciles_records. However,
        # NaNs are present in org_records. Python's json.JSONEncoder will serialise
        # NaNs, but JavaScript's JSON.parse won't deserialise them. Consequently, we
        # have to convert NaNs to Nones ourselves.
        nans_to_nones(org_records)
    else:
        org_records = []

    return org_records


def prescribing_all_orgs(request):
    analysis = Analysis.from_params(request.GET)
    odm = analysis.get_organisation_date_matrix()
    org = _get_org(analysis)

    all_orgs_records = list(odm.to_records(row_name="org", col_name="month"))
    nans_to_nones(all_orgs_records)
    org_records = _get_org_records(odm, org)

    if org is None:
        org_type = "icb"
    else:
        org_type = org.org_type

    return JsonResponse(
        {"all_orgs": all_orgs_records, "org": org_records, "org_type": org_type}
    )


def prescribing_deciles(request):
    analysis = Analysis.from_params(request.GET)
    odm = analysis.get_organisation_date_matrix()
    org = _get_org(analysis)
    cdm = get_centiles(odm)

    deciles_records = list(cdm.to_records(row_name="centile", col_name="month"))
    org_records = _get_org_records(odm, org)

    if org is None:
        org_type = "icb"
    else:
        org_type = org.org_type

    return JsonResponse(
        {"deciles": deciles_records, "org": org_records, "org_type": org_type}
    )


class JsonResponse(DjangoJsonResponse):
    def __init__(self, *args, **kwargs):
        kwargs["encoder"] = JSONEncoder
        kwargs["json_dumps_params"] = {"allow_nan": False}
        super().__init__(*args, **kwargs)


class JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, Org):
            return o.id
        return super().default(o)


def nans_to_nones(records):
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
