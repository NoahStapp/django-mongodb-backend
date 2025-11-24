from django.contrib.gis.db import models


class City(models.Model):
    name = models.CharField(max_length=30)
    point = models.PointField()


class Zipcode(models.Model):
    code = models.CharField(max_length=10)
    poly = models.PolygonField(geography=True)
