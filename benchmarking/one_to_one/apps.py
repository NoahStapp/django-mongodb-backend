from django.apps import AppConfig


class OneToOneConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "benchmarking.one_to_one"
