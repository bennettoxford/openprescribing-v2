from django.shortcuts import render

from openprescribing.data import rxdb


def index(request):
    bnf_code = "0601023AW"  # Semaglutide

    sql = f"""
    SELECT practice_id, date_id, items AS value
    FROM prescribing
    WHERE bnf_code LIKE '{bnf_code}%'
    """

    with rxdb.get_cursor() as cursor:
        pdm = rxdb.get_practice_date_matrix(cursor, sql)

    labels = pdm.col_labels
    values = pdm.values.sum(axis=0)

    table = zip(labels, values)

    ctx = {"table": table}

    return render(request, "index.html", ctx)
