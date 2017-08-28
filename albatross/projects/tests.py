from django.test import TestCase

from .models import Project, Category, Item


class CategoryTestCase(TestCase):
    def setUp(self):
        project = Project.objects.create(name='My Project')
        Category.objects.create(name='Backend', project=project)

    def test_no_items_in_category(self):
        category = Category.objects.get(name='Backend')
        self.assertEqual(category.items.all().count(), 0)
        self.assertEqual(category.actual, 0)
        self.assertEqual(category.estimated, 0)

    def test_items_in_category(self):
        category = Category.objects.get(name='Backend')
        Item.objects.create(description='Models', actual=1, estimated=7, category=category)
        Item.objects.create(description='Deployment', actual=5, estimated=15, category=category)

        self.assertEqual(category.items.all().count(), 2)
        self.assertEqual(category.actual, 6)
        self.assertEqual(category.estimated, 22)

    def test_add_item_updates_actual_estimate(self):
        category = Category.objects.get(name='Backend')
        Item.objects.create(description='Project', actual=0, estimated=10, category=category)
        self.assertEqual(category.items.all().count(), 1)
        self.assertEqual(category.actual, 0)
        self.assertEqual(category.estimated, 10)

        Item.objects.create(description='Users', actual=3, estimated=15, category=category)
        self.assertEqual(category.items.all().count(), 2)
        self.assertEqual(category.actual, 3)
        self.assertEqual(category.estimated, 25)
