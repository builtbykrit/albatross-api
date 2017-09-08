from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.validators import MaxValueValidator, MinValueValidator
from teams.models import Team
from toggl.hooks import hookset as toggl_hookset


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
        aggregate_results = self.categories.aggregate(
            sum=Coalesce(Sum('items__estimated'), 0))
        sum = aggregate_results['sum']
        estimated = sum * (1 + (self.buffer / 100))
        return int(round(estimated))

    def update_actual(self):
        toggl_hookset.update_project_line_item_times(
            self=toggl_hookset,
            api_key=self.team.creator.profile.toggl_api_key,
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
