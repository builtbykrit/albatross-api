from django.test import TestCase

from .models import Project, Category


class CategoryTestCase(TestCase):
    def setUp(self):
        project = Project.objects.create(name='My Project')
        Category.objects.create(name='Design', project=project)

    def test_no_items_in_category(self):
        category = Category.objects.get(name='Design')
        self.assertEqual(category.items.all().count(), 0)
        self.assertEqual(category.actual, 0)
        self.assertEqual(category.estimated, 0)
