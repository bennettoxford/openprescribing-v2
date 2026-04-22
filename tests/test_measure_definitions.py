from openprescribing.data.measures import all_measure_details, load_measure


def test_load_all_measures():
    for measure in all_measure_details():
        load_measure(measure["name"])
