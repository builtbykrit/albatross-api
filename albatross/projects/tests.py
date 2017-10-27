from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
import json

from .models import Project, Category, Item
from teams.models import Team


class CategoryModelTestCase(TestCase):
    def setUp(self):
        Team.objects.create(name='Krit', creator_id=1)
        project = Project.objects.create(name='My Project', team=Team.objects.get(name='Krit'))
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
        Project.objects.create(name='My Project', team=Team.objects.get(name='Krit'))

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

    def test_change_buffer_updates_estimate(self):
        project = Project.objects.get(name='My Project')
        category_backend = Category.objects.create(name='Backend', project=project)
        category_frontend = Category.objects.create(name='Frontend', project=project)

        Item.objects.create(description='Deployment', actual=5, estimated=20, category=category_backend)
        Item.objects.create(description='User Page', actual=2, estimated=7, category=category_frontend)

        self.assertEqual(project.estimated, 27)
        project.buffer = 20
        self.assertEqual(project.estimated, Decimal("32.4"))


class ProjectViewTests(APITestCase):
    def setUp(self):
        Team.objects.create(name='Krit', creator_id=1)
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        Team.objects.create(name='Kritters', creator=user)
        self.client.force_authenticate(user=user)

    def test_unauthenticated_user_projects_response(self):
        client = APIClient()
        response = client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_user_create_project_response(self):
        client = APIClient()
        data = {
            'data': {
                'attributes': {
                    'name': 'My Project'
                },
                'type': 'projects'
            }
        }
        response = client.post(data=json.dumps(data),
                               path=reverse('project-list'),
                               content_type='application/vnd.api+json'
                               )
        self.assertEqual(response.status_code, 401)

    def test_no_projects_response(self):
        '''
        GET /projects/
        '''
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_response['data'], [])

    def test_projects_response(self):
        '''
        GET /projects/
        '''
        Project.objects.create(name='My Project', team=Team.objects.get(name='Kritters'))
        Project.objects.create(name='Albatross', team=Team.objects.get(name='Kritters'))

        response = self.client.get(reverse('project-list'))
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

    def test_projects_response_only_returns_own_projects(self):
        '''
        GET /projects/
        '''

        user = User.objects.create_user(
            email='austin@builtbykrit.com',
            first_name='Austin',
            last_name='Price',
            password='password125',
            username='austin@builtbykrit.com'
        )
        team = Team.objects.create(name='The Other Guys', creator=user)
        Project.objects.create(name='New Project', team=team)
        Project.objects.create(name='Albatross', team=team)

        project = Project.objects.create(name='My Project', team=Team.objects.get(name='Kritters'))

        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(json_response['data']), 1)
        project_data = json_response['data'][0]
        project_attributes = project_data['attributes']
        self.assertEqual(project_attributes['name'], project.name)

    def test_get_one_project(self):
        '''
        GET /projects/:id
        '''

        project = Project.objects.create(name='My Project', buffer=10, team=Team.objects.get(name='Kritters'))
        category = Category.objects.create(name='Design', project=project)
        Item.objects.create(description='Login', estimated=10, actual=2, category=category)
        Item.objects.create(description='Login', estimated=10, actual=3, category=category)

        response = self.client.get(reverse('project-detail', args=(project.id,)))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        project_data = json_response['data']
        project_attributes = project_data['attributes']
        project_relationships = project_data['relationships']

        self.assertIn('categories', project_relationships)
        self.assertTrue(project_attributes['created_at'])
        self.assertTrue(project_attributes['updated_at'])
        self.assertTrue(project_attributes['name'])
        self.assertEqual(project_attributes['estimated'], 22)
        self.assertEqual(project_attributes['actual'], 5)
        self.assertEqual(project_attributes['buffer'], 10)

    def test_no_project_found(self):
        '''
        /GET projects/:id
        '''

        response = self.client.get(reverse('project-detail', args=(1000,)))
        self.assertEqual(response.status_code, 404)

    def test_create_project(self):
        data = {
            'data': {
                'attributes': {
                    'name': 'My Project'
                },
                'type': 'projects'
            }
        }
        response = self.client.post(data=json.dumps(data),
                                    path=reverse('project-list'),
                                    content_type='application/vnd.api+json'
                                    )
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.content.decode('utf-8'))
        project_data = json_response['data']
        self.assertEqual(Project.objects.get(id=project_data['id']).name, 'My Project')

        response_list = self.client.get(path=reverse('project-list'),
                                        content_type='application/vnd.api+json')
        self.assertEqual(response_list.status_code, 200)

        json_response = json.loads(response_list.content.decode('utf-8'))
        self.assertEqual(len(json_response['data']), 1)

    def test_change_project_name(self):
        '''
        PATCH /projects/:id
        '''

        project = Project.objects.create(name='My Project', team=Team.objects.get(name='Kritters'))
        data = {
            'data': {
                'id': project.id,
                'attributes': {
                    'name': 'Albatross'
                },
                'type': 'projects'
            }
        }
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('project-detail', args=(project.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.get(id=project.id).name, 'Albatross')

    def test_change_project_buffer(self):
        '''
        PATCH /projects/:id
        '''

        project = Project.objects.create(name='My Project', team=Team.objects.get(name='Kritters'))
        category = Category.objects.create(name='Design', project=project)
        Item.objects.create(description='Login', estimated=10, actual=2, category=category)
        Item.objects.create(description='Login', estimated=10, actual=3, category=category)

        data = {
            'data': {
                'id': project.id,
                'attributes': {
                    'buffer': 15
                },
                'type': 'projects'
            }
        }
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('project-detail', args=(project.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(id=project.id)

        self.assertEqual(project.buffer, 15)
        self.assertEqual(project.estimated, 23)

    def test_project_categories_relationship(self):
        """
        Tests the categories relationship on project only returns categories that belong to a project
        """

        project1 = Project.objects.create(name='My Project', team=Team.objects.get(name='Kritters'))
        project2 = Project.objects.create(name='My Other Project', team=Team.objects.get(name='Kritters'))
        Category.objects.create(name='Design', project=project1)
        Category.objects.create(name='Development', project=project1)
        category_product = Category.objects.create(name='Product', project=project2)

        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(json_response['data']), 2)
        project2_data = json_response['data'][0]
        project1_data = json_response['data'][1]

        project1_relationships = project1_data['relationships']
        project1_relationships_data = project1_relationships['categories']['data']
        self.assertEqual(len(project1_relationships_data), 2)

        project2_relationships = project2_data['relationships']
        project2_relationships_data = project2_relationships['categories']['data']
        self.assertEqual(len(project2_relationships_data), 1)
        self.assertEqual(int(project2_relationships_data[0]['id']), category_product.id)

    def test_update_actual_time_without_integrating_a_service_first(self):
        project = Project.objects.create(name='My Project',
                                         team=Team.objects.get(
                                             name='Kritters'))
        response = self.client.post(reverse('project-update-actual-time',
                                            args=(project.id,)))
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'errors' in json_data
        assert 'detail' in json_data['errors'][0]
        assert json_data['errors'][0]['detail'] == 'Please login with ' \
                                                   'Harvest or provide ' \
                                                   'a Toggl API key.'


class CategoryViewTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        team = Team.objects.create(name='Kritters', creator=user)
        self.client.force_authenticate(user=user)
        project = Project.objects.create(name='My Project', team=team)
        category = Category.objects.create(name='Frontend', project=project)
        Item.objects.create(description='Login', actual=5, estimated=20, category=category)

    def test_unauthenticated_user_category_response(self):
        client = APIClient()
        response = client.get(reverse('category-detail', args=(1,)))
        self.assertEqual(response.status_code, 401)

    def test_create_category(self):
        '''
        POST /categories
        '''

        project = Project.objects.get(name='My Project')
        data = {
            'data': {
                'attributes': {
                    'name': 'Design'
                },
                'relationships': {
                    'project': {
                        'data': {
                            'id': project.id,
                            'type': 'projects'
                        }
                    }
                },
                'type': 'categories'
            }
        }
        response = self.client.post(data=json.dumps(data),
                                    path=reverse('category-list'),
                                    content_type='application/vnd.api+json'
                                    )

        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.content.decode('utf-8'))
        category_data = json_response['data']
        self.assertEqual(Category.objects.get(id=category_data['id']).name, 'Design')
        self.assertEqual(project.categories.all().count(), 2)

    def test_get_one_category(self):
        '''
        GET /categories/:id
        '''

        project = Project.objects.get(name='My Project')
        category = Category.objects.create(name='Development', project=project)
        Item.objects.create(description='Login', estimated=10, actual=2, category=category)
        Item.objects.create(description='Settings', estimated=10, actual=3, category=category)

        response = self.client.get(reverse('category-detail', args=(category.id,)))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        category_data = json_response['data']
        category_attributes = category_data['attributes']
        category_relationships = category_data['relationships']
        category_included = json_response['included']

        self.assertEqual(len(category_included), 2)
        self.assertIn('items', category_relationships)
        self.assertEqual(len(category_relationships['items']['data']), 2)
        self.assertTrue(category_attributes['created_at'])
        self.assertTrue(category_attributes['updated_at'])
        self.assertTrue(category_attributes['name'])
        self.assertEqual(category_attributes['estimated'], 20)
        self.assertEqual(category_attributes['actual'], 5)

    def test_change_category_name(self):
        '''
        PATCH /categories/:id
        '''
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
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('category-detail', args=(category.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.get(id=category.id).name, 'Backend')

    def test_category_items_relationship(self):
        """
        Tests the items relationship on category only returns items that belong to a category
        """

        project = Project.objects.get(name='My Project', team=Team.objects.get(name='Kritters'))
        category = Category.objects.create(name='Wireframes', project=project)
        item_users = Item.objects.create(description='Users', estimated=3, actual=1, category=category)
        item_settings = Item.objects.create(description='Settings', estimated=2, actual=1, category=category)

        response = self.client.get(reverse('category-detail', args=(category.id,)))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.content.decode('utf-8'))
        category_data = json_response['data']
        category_included = json_response['included']
        self.assertEqual(len(category_included), 2)

        category_relationships = category_data['relationships']
        category_relationships_data = category_relationships['items']['data']

        self.assertEqual(len(category_relationships_data), 2)

        ids = []
        for item_data in category_relationships_data:
            ids.append(int(item_data['id']))

        self.assertIn(item_users.id, ids)
        self.assertIn(item_settings.id, ids)


class ItemViewTests(APITestCase):
    CATEGORY_NAME = 'Frontend'
    PROJECT_NAME = 'My Project'
    ITEM_DESCRIPTION = 'Login'

    def setUp(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        team = Team.objects.create(name='Kritters', creator=user)
        self.client.force_authenticate(user=user)
        project = Project.objects.create(name=self.PROJECT_NAME, team=team)
        category = Category.objects.create(name=self.CATEGORY_NAME, project=project)
        Item.objects.create(description=self.ITEM_DESCRIPTION, actual=5, estimated=20, category=category)

    def test_unauthenticated_user_category_response(self):
        client = APIClient()
        response = client.get(reverse('item-detail', args=(1,)))
        self.assertEqual(response.status_code, 401)

    def test_create_item(self):
        '''
        POST /items
        '''

        category = Category.objects.get(name=self.CATEGORY_NAME)
        data = {
            'data': {
                'attributes': {
                    'description': 'Login',
                    'estimated': 5,
                    'actual': 0,
                },
                'relationships': {
                    'category': {
                        'data': {
                            'id': category.id,
                            'type': 'categories'
                        }
                    }
                },
                'type': 'items'
            }
        }
        response = self.client.post(data=json.dumps(data),
                                    path=reverse('item-list'),
                                    content_type='application/vnd.api+json'
                                    )

        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.content.decode('utf-8'))
        item_data = json_response['data']
        self.assertEqual(Item.objects.get(id=item_data['id']).description, 'Login')
        self.assertEqual(category.items.all().count(), 2)
        self.assertEqual(category.estimated, 25)
        self.assertEqual(category.actual, 5)

    def test_change_item_description(self):
        item = Item.objects.get(description=self.ITEM_DESCRIPTION)
        data = {
            'data': {
                'id': item.id,
                'attributes': {
                    'description': 'Register'
                },
                'type': 'items'
            }
        }
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('item-detail', args=(item.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.get(id=item.id).description, 'Register')

    def test_change_item_actual(self):
        item = Item.objects.get(description=self.ITEM_DESCRIPTION)
        data = {
            'data': {
                'id': item.id,
                'attributes': {
                    'actual': 15
                },
                'type': 'items'
            }
        }
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('item-detail', args=(item.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.get(id=item.id).actual, 15)
        self.assertEqual(Category.objects.get(name=self.CATEGORY_NAME).actual, 15)
        self.assertEqual(Project.objects.get(name=self.PROJECT_NAME).actual, 15)

    def test_change_item_estimated(self):
        item = Item.objects.get(description=self.ITEM_DESCRIPTION)
        data = {
            'data': {
                'id': item.id,
                'attributes': {
                    'estimated': 30
                },
                'type': 'items'
            }
        }
        response = self.client.patch(data=json.dumps(data),
                                     path=reverse('item-detail', args=(item.id,)),
                                     content_type='application/vnd.api+json'
                                     )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.get(id=item.id).estimated, 30)
        self.assertEqual(Category.objects.get(name=self.CATEGORY_NAME).estimated, 30)
        self.assertEqual(Project.objects.get(name=self.PROJECT_NAME).estimated, 30)
