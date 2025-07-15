from django.db import models

from benchmarking.common.models import Author


class BookOneToOne(models.Model):
    title = models.CharField(max_length=100)
    author = models.OneToOneField(Author, on_delete=models.CASCADE)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()

class BookOneToMany(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()

class BookManyToMany(models.Model):
    title = models.CharField(max_length=100)
    author = models.ManyToManyField(Author)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()