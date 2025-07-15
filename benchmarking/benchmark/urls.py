"""
URL configuration for benchmark project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from benchmarking.filter_operations.views import populate_data, benchmark_filter_operations, clear_data

urlpatterns = [
    path("filter_operations/populate_data/<int:n>/<str:data_type>", populate_data,
         name="populate_data"),
    path("filter_operations/benchmark_filter_operations/<str:data_type>", benchmark_filter_operations, name="benchmark_filter_operations"),
    path("clear_data/", clear_data, name="clear_data"),
    path("admin/", admin.site.urls),
]
