from django.db import models


class SmallFlatModel(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.CharField(max_length=100)
    field3 = models.CharField(max_length=100)
    field4 = models.CharField(max_length=100)
    field5 = models.CharField(max_length=100)
    field6 = models.CharField(max_length=100)
    field7 = models.CharField(max_length=100)
    field8 = models.IntegerField()
    field9 = models.IntegerField()
    field10 = models.IntegerField()
    field11 = models.IntegerField()
    field12 = models.IntegerField()
    field13 = models.IntegerField()
