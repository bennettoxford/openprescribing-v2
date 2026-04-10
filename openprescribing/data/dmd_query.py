from django.db.models import Q

from openprescribing.data.models.dmd import OntFormRoute


def search_routes(route_list):
    query = Q()
    for route in route_list:
        query |= Q(descr__endswith=f".{route}")
    form_routes = OntFormRoute.objects.filter(query)
    # if route_list and not form_routes:
    #     # sentinel value so that a route with no matches will not match
    #     form_routes = [{"cd": "99999999999"}]

    return form_routes
