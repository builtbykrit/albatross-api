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
        '''
        GET /projects/
        '''
        client = Client()
        response = client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_response['data'], [])

    def test_projects_response(self):
        '''
        GET /projects/
        '''
        Project.objects.create(name='My Project')
        Project.objects.create(name='Albatross')
        client = Client()
        response = client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(json_response['data']), 2)
        project_data = json_response['data'][0]
        project_attributes = project_data['attributes']

        # Assert the correct attributes are returned
        self.assertTrue(project_attributes['created_at'])
        self.assertTrue(project_attributes['updated_at'])
        self.assertTrue(project_attributes['name'])
        self.assertEqual(project_attributes['estimated'], 0)
        self.assertEqual(project_attributes['actual'], 0)

    def test_get_one_project(self):
        '''
        GET /projects/:id
        '''

        project = Project.objects.create(name='My Project')
        category = Category.objects.create(name='Design', project=project)
        Item.objects.create(description='Login', estimated=10, actual=2, category=category)
        Item.objects.create(description='Login', estimated=10, actual=3, category=category)

        client = Client()
        response = client.get(reverse('project-detail', args=(project.id,)))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        project_data = json_response['data']
        project_attributes = project_data['attributes']
        project_relationships = project_data['relationships']
        project_included = json_response['included']

        self.assertEqual(len(project_included), 1)
        self.assertIn('categories', project_relationships)
        self.assertTrue(project_attributes['created_at'])
        self.assertTrue(project_attributes['updated_at'])
        self.assertTrue(project_attributes['name'])
        self.assertEqual(project_attributes['estimated'], 20)
        self.assertEqual(project_attributes['actual'], 5)

    def test_no_project_found(self):
        '''
        /GET projects/:id
        '''

        client = Client()
        response = client.get(reverse('project-detail', args=(1000,)))
        self.assertEqual(response.status_code, 404)

    def test_change_project_name(self):
        '''
        PATCH /projects/:id
        '''

        project = Project.objects.create(name='My Project')
        client = Client()
        data = {
            'data': {
                'id': project.id,
                'attributes': {
                    'name': 'Albatross'
                },
                'type': 'projects'
            }
        }
        response = client.patch(data=json.dumps(data),
                                path=reverse('project-detail', args=(project.id,)),
                                content_type='application/vnd.api+json'
                                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.get(id=project.id).name, 'Albatross')

class CategoryViewTests(TestCase):

    def setUp(self):
        project = Project.objects.create(name='My Project')
        category = Category.objects.create(name='Frontend', project=project)
        Item.objects.create(description='Login', actual=5, estimated=20, category=category)

    def test_change_category_name(self):
        '''
        PATCH /categories/:id
        '''

        client = Client()
        category = Category.objects.get(name='Frontend')
        data = {
            'data': {
                'id': category.id,
                'attributes': {
                    'name': 'Backend'
                },
                'type': 'categories'
            }
        }
        response = client.patch(data=json.dumps(data),
                                path=reverse('category-detail', args=(category.id,)),
                                content_type='application/vnd.api+json'
                                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.get(id=category.id).name, 'Backend')