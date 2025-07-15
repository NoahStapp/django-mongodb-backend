import time

from django.db import connection, reset_queries
from django.db.models import Q
from django.http import HttpResponse
import json

from benchmarking.common.models import Author
from benchmarking.filter_operations.models import BookOneToOne, BookOneToMany, BookManyToMany
from benchmarking.filter_operations.populate_data import populate_data as _populate_data


def populate_data(request, n, data_type):
    _populate_data(data_type, n)
    book_class = None
    if data_type == "one_to_one":
        book_class = BookOneToOne
    elif data_type == "one_to_many":
        book_class = BookOneToMany
    elif data_type == "many_to_many":
        book_class = BookManyToMany
    return HttpResponse(f"Generated {data_type} data with {Author.objects.count()} authors and {book_class.objects.count()} books.")

def clear_data(request):
    Author.objects.all().delete()
    BookOneToOne.objects.all().delete()
    BookOneToMany.objects.all().delete()
    BookManyToMany.objects.all().delete()
    return HttpResponse("Cleared all data!")


def benchmark_filter_operations(request, data_type):
    authors = list(Author.objects.all())
    book_class = None
    if data_type == "one_to_one":
        book_class = BookOneToOne
    if data_type == "one_to_many":
        book_class = BookOneToMany
    elif data_type == "many_to_many":
        book_class = BookManyToMany
    stats = {}
    # Filter by exact match on foreign key
    start = time.monotonic()
    for author in authors:
        list(book_class.objects.filter(author__name=author.name)) # use list() to force evaluation
    time_taken = time.monotonic() - start
    query_time = sum([float(query["time"]) for query in connection.queries])
    sub_stats = {}
    sub_stats["query_time"] = f"{query_time} seconds"
    sub_stats["latency"] = f"{time_taken - query_time} seconds"
    sub_stats["throughput"] = f"{len(connection.queries) / time_taken} queries/second"
    stats["filter_by_exact_match_fk"] = sub_stats

    reset_queries()

    # Filter by partial match on foreign key
    start = time.monotonic()
    for author in authors:
        list(book_class.objects.filter(author__name=author.name[0:5])) # use list() to force evaluation
    time_taken = time.monotonic() - start
    query_time = sum([float(query["time"]) for query in connection.queries])
    sub_stats = {}
    sub_stats["query_time"] = f"{query_time} seconds"
    sub_stats["latency"] = f"{time_taken - query_time} seconds"
    sub_stats["throughput"] = f"{len(connection.queries) / time_taken} queries/second"
    stats["filter_by_partial_match_fk"] = sub_stats

    reset_queries()

    # Filter by publish date
    start = time.monotonic()
    list(book_class.objects.filter(publish_date__range=["1980-01-01", "2000-01-01"])) # use list() to force evaluation
    time_taken = time.monotonic() - start
    query_time = sum([float(query["time"]) for query in connection.queries])
    sub_stats = {}
    sub_stats["query_time"] = f"{query_time} seconds"
    sub_stats["latency"] = f"{time_taken - query_time} seconds"
    sub_stats["throughput"] = f"{len(connection.queries) / time_taken} queries/second"
    stats["filter_by_date_range"] = sub_stats

    reset_queries()

    # Filter by OR on genre and AND on author partial name
    start = time.monotonic()
    for author in authors:
        list(book_class.objects.filter(Q(genre="Fantasy") | Q(genre="Sci-Fi"), author__name=author.name[0:5])) # use list() to force evaluation
    time_taken = time.monotonic() - start
    query_time = sum([float(query["time"]) for query in connection.queries])
    sub_stats = {}
    sub_stats["query_time"] = f"{query_time} seconds"
    sub_stats["latency"] = f"{time_taken - query_time} seconds"
    sub_stats["throughput"] = f"{len(connection.queries) / time_taken} queries/second"
    stats["filter_by_complex_filters"] = sub_stats


    return HttpResponse(json.dumps(stats, indent=2), content_type="application/json")

