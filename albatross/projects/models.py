from django.db import models


class Project(models.Model):
    name = models.CharField()


class Category(models.Model):
    name = models.CharField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class Item(models.Model):
    actual = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.CharField()
    estimated = models.IntegerField()
