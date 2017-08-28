from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class Project(models.Model):
    name = models.CharField(max_length=200)

    @property
    def actual(self):
        aggregate_results = self.categories.aggregate(sum=Coalesce(Sum('items__actual'), 0))
        return aggregate_results['sum']

    @property
    def estimated(self):
        aggregate_results = self.categories.aggregate(sum=Coalesce(Sum('items__estimated'), 0))
        return aggregate_results['sum']


class Category(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='categories')

    @property
    def actual(self):
        aggregate_results = self.items.aggregate(sum=Coalesce(Sum('actual'), 0))
        return aggregate_results['sum']

    @property
    def estimated(self):
        aggregate_results = self.items.aggregate(sum=Coalesce(Sum('estimated'), 0))
        return aggregate_results['sum']


class Item(models.Model):
    actual = models.DecimalField(max_digits=7, decimal_places=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    estimated = models.DecimalField(max_digits=7, decimal_places=1)
