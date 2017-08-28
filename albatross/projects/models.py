from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)


class Category(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class Item(models.Model):
    actual = models.DecimalField(max_digits=7, decimal_places=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    estimated = models.DecimalField(max_digits=7, decimal_places=1)
