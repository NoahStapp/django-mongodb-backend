from django.http import HttpResponse

from benchmarking.one_to_one.populate_data import populate_data


def populate_data_one_to_one(request):
    populate_data("one_to_one")
    return HttpResponse("Generated one-to-one data")

def filter_by_exact_match(request):
    return HttpResponse("MongoDB filter_by_exact_match benchmark")
