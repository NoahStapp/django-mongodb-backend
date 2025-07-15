import random
import time

import numpy as np

from django.db import connection, reset_queries
from django.db.models import Q
from django.http import HttpResponse
import json

from benchmarking.common.models import Author
from benchmarking.filter_operations.models import BookOneToOne, BookOneToMany, BookManyToMany
from benchmarking.filter_operations.populate_data import populate_data as _populate_data, GENRES


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

def _run_benchmark(benchmark_function, setup_function, trials):
    runs = []
    total_queries = []
    for _ in range(trials):
        setup_function()
        trial_stats = {}

        start = time.monotonic()
        benchmark_function()
        trial_stats["latency"] = time.monotonic() - start
        trial_stats["throughput"] = len(connection.queries) / trial_stats["latency"]
        total_queries.extend([float(query["time"]) for query in connection.queries])
        runs.append(trial_stats)
        reset_queries()

    run_stats = {}
    run_stats["p50 query execution time"] = np.percentile(total_queries, 50)
    run_stats["p75 query execution time"] = np.percentile(total_queries, 75)
    run_stats["p90 query execution time"] = np.percentile(total_queries, 90)
    run_stats["p99 query execution time"] = np.percentile(total_queries, 99)
    run_stats["Throughput"] = f"{sum([float(stats["throughput"]) for stats in runs]) / len(runs)} ops/s"
    run_stats["Latency"] = f"{sum([float(stats["latency"]) for stats in runs]) / len(runs)} seconds"

    return run_stats


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

    ### Basic Filter Operations

    # Filter by exact match
    def benchmark_function():
        list(book_class.objects.filter(genre=random.choice(GENRES))) # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, lambda: None, 10)
    stats["filter_by_exact_match"] = run_stats

    # Filter by partial match
    def benchmark_function():
        list(book_class.objects.filter(genre__contains=random.choice(GENRES)[0:2])) # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, lambda: None, 10)
    stats["filter_by_partial_match"] = run_stats

    # Filter by publish date
    setup_function = lambda: random.shuffle(authors)
    def benchmark_function():
        list(book_class.objects.filter(
            publish_date__range=["1980-01-01", "2000-01-01"]))  # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, setup_function, 10)
    stats["filter_by_date_range"] = run_stats

    # Filter by OR on genre as well as AND on date range
    def benchmark_function():
        list(book_class.objects.filter(Q(genre=random.choice(GENRES)) | Q(genre=random.choice(GENRES)), publish_date__range=["1980-01-01", "2000-01-01"]))  # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, lambda: None, 10)
    stats["filter_by_complex_filters"] = run_stats

    ### Join/Foreign Key Usage
    # Filter by exact match on foreign key
    setup_function = lambda: random.shuffle(authors)
    def benchmark_function():
        for author in authors:
            list(book_class.objects.filter(author__name=author.name)) # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, setup_function, 10)
    stats["filter_by_exact_match_fk"] = run_stats

    # Filter by partial match on foreign key
    setup_function = lambda: random.shuffle(authors)
    def benchmark_function():
        for author in authors:
            list(book_class.objects.filter(author__name__contains=author.name[0:5]))  # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, setup_function, 10)
    stats["filter_by_partial_match_fk"] = run_stats

    # Filter by OR on genre as well as AND on author partial name
    setup_function = lambda: random.shuffle(authors)
    def benchmark_function():
        for author in authors:
            list(book_class.objects.filter(Q(genre="Fantasy") | Q(genre="Sci-Fi"), author__name__contains=author.name[0:5]))  # use list() to force evaluation

    run_stats = _run_benchmark(benchmark_function, setup_function, 10)
    stats["filter_by_complex_filters_fk"] = run_stats

    return HttpResponse(json.dumps(stats, indent=2), content_type="application/json")

