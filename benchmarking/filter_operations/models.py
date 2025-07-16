from django.db import models

from benchmarking.common.models import Author


class BookOneToOne(models.Model):
    title = models.CharField(max_length=100)
    author = models.OneToOneField(Author, on_delete=models.CASCADE)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["genre"], name="one_to_one_genre_idx"),
            models.Index(fields=["publish_date"], name="one_to_one_publish_date_idx")
        ]

class BookOneToMany(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["genre"], name="one_to_many_genre_idx"),
            models.Index(fields=["publish_date"], name="one_to_many_publish_date_idx")
        ]

class BookManyToMany(models.Model):
    title = models.CharField(max_length=100)
    author = models.ManyToManyField(Author)
    genre = models.CharField(max_length=15)
    publish_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["genre"], name="many_to_many_genre_idx"),
            models.Index(fields=["publish_date"], name="many_to_many_publish_date_idx")
        ]
