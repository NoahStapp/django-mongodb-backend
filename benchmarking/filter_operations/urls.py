from django.urls import path

from benchmarking.filter_operations import views

urlpatterns = [
    path("populate_data/<int:n>/<str:data_type>", views.populate_data, name="populate_data"),
    path("benchmark_filter_operations/<str:data_type>", views.benchmark_filter_operations, name="benchmark_filter_operations"),
    path("clear_data/", views.clear_data, name="clear_data"),
]