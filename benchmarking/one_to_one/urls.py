from django.urls import path

from benchmarking.one_to_one import views

urlpatterns = [
    path("", views.populate_data_one_to_one, name="populate_data_one_to_one"),
]