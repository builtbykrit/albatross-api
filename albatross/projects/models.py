from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.validators import MaxValueValidator, MinValueValidator
from teams.models import Team


class CommonInfo(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(CommonInfo):
    buffer = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    name = models.CharField(max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')

    @property
    def actual(self):
        aggregate_results = self.categories.aggregate(sum=Coalesce(Sum('items__actual'), 0))
        return aggregate_results['sum']

    @property
    def estimated(self):
        aggregate_results = self.categories.aggregate(sum=Coalesce(Sum('items__estimated'), 0))
        sum = aggregate_results['sum']
        estimated = sum * (1 + (self.buffer / 100))
        return int(round(estimated))

    class JSONAPIMeta:
        resource_name = "projects"


class Category(CommonInfo):
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

    class JSONAPIMeta:
        resource_name = "categories"


class Item(CommonInfo):
    actual = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    estimated = models.IntegerField()

    class JSONAPIMeta:
        resource_name = "items"
