import decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib.postgres.fields import ArrayField
from picklefield.fields import PickledObjectField
from teams.models import Team


class CommonInfo(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(CommonInfo):
    archived = models.BooleanField(default=False)
    buffer = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_weeks_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_imported_date = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=200)
    previous_weeks_hours = ArrayField(PickledObjectField(), blank=True, default=list)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')

    @property
    def actual(self):
        aggregate_results = self.categories.aggregate(sum=Coalesce(Sum('items__actual'), 0))
        return aggregate_results['sum']

    @property
    def estimated(self):
        aggregate_results = self.categories.aggregate(
            sum=Coalesce(Sum('items__estimated'), 0))
        sum = aggregate_results['sum']
        buffer_percentage = decimal.Decimal(1 + (self.buffer / 100))
        estimated = sum * buffer_percentage
        return round(estimated, 2)

    def update_actual(self, api_key, hookset):
        hookset.update_project_line_item_times(
            self=hookset,
            api_credentials=api_key,
            project_to_update=self
        )

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
    actual = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    estimated = models.DecimalField(max_digits=10, decimal_places=2)

    class JSONAPIMeta:
        resource_name = "items"
