from django.test import TestCase
from django.test import Client
from django.urls import reverse
import json

from .models import Project, Category, Item


class CategoryModelTestCase(TestCase):
    def setUp(self):
        project = Project.objects.create(name='My Project')
        Category.objects.create(name='Backend', project=project)

    def test_no_item(self):
        """
        Tests actual and estimated are 0 on an empty category
        """

        category = Category.objects.get(name='Backend')
        self.assertEqual(category.items.all().count(), 0)
        self.assertEqual(category.actual, 0)
        self.assertEqual(category.estimated, 0)

    def test_add_item_updates_actual_estimated(self):
        """
        Tests actual and estimated updating when items are added to a category
         """

        category = Category.objects.get(name='Backend')
        Item.objects.create(description='Project', actual=0, estimated=10, category=category)
        self.assertEqual(category.items.all().count(), 1)
        self.assertEqual(category.actual, 0)
        self.assertEqual(category.estimated, 10)

        Item.objects.create(description='Users', actual=3, estimated=15, category=category)
        self.assertEqual(category.items.all().count(), 2)
        self.assertEqual(category.actual, 3)
        self.assertEqual(category.estimated, 25)


class ProjectModelTestCases(TestCase):
    def setUp(self):
        Project.objects.create(name='My Project')

    def test_no_categories(self):
        """
        Tests actual and estimated are 0 on an empty project
        """

        project = Project.objects.get(name='My Project')
        self.assertEqual(project.categories.all().count(), 0)
        self.assertEqual(project.actual, 0)
        self.assertEqual(project.estimated, 0)

    def test_add_categories_updates_actual_estimated(self):
        """
        Tests actual and estimated updating when categories are added to a project
        """

        project = Project.objects.get(name='My Project')
        category_backend = Category.objects.create(name='Backend', project=project)
        category_frontend = Category.objects.create(name='Frontend', project=project)

        self.assertEqual(project.categories.count(), 2)
        self.assertEqual(project.actual, 0)
        self.assertEqual(project.estimated, 0)

        Item.objects.create(description='Deployment', actual=5, estimated=20, category=category_backend)
        Item.objects.create(description='User Page', actual=2, estimated=7, category=category_frontend)

        self.assertEqual(project.categories.count(), 2)
        self.assertEqual(project.actual, 7)
        self.assertEqual(project.estimated, 27)


class ProjectViewTests(TestCase):

    def test_no_projects_response(self):
        client = Client()
        response = client.get(reverse('projects-list'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['data'], [])

    def test_one_project_response(self):
        Project.objects.create(name='My Project')
        client = Client()
        response = client.get(reverse('projects-list'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response['data']), 1)