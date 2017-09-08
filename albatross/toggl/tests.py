import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from authentication.models import UserProfile
from projects.models import Category, Item, Project
from teams.models import Team

class TogglTestCase(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.user.profile.toggl_api_key = '65190d62cba42daab81469efd5a7f580'
        self.user.profile.save()
        self.client.force_authenticate(user=self.user)

        # Create team to own project
        team = Team.objects.create(
            creator=self.user,
            name='Test Team'
        )

        # Create project
        self.project = Project.objects.create(
            buffer=0,
            name='Albatross MVP',
            team=team
        )
        category = Category.objects.create(
            name='Back end dev',
            project=self.project
        )
        items = [('Authentication',10),
                 ('Categories',8),
                 ('Deployment',25),
                 ('Line Items',8),
                 ('Projects',6),
                 ('Settings',3),
                 ('Signup',2.5),
                 ('Summary',3),
                 ('Teams',6),
                 ('Toggl Integration',6),
                 ('Users',5),
                 ('Invitations',2.5)]
        for item in items:
            Item.objects.create(
                actual=0,
                category=category,
                description=item[0],
                estimated=item[1]
            )

    def test_import_project_data_from_toggl(self):
         response = self.client.post(
             reverse('project-update-actual-time', args=(self.project.id,))
         )
         self.assertEqual(response.status_code, 200)
         json_data = json.loads(response.content.decode('utf-8'))

         assert 'data' in json_data
         data = json_data['data']
         assert 'attributes' in data
         assert 'id' in data
         assert 'relationships' in data
         assert 'type' in data
         assert data['id'] == str(self.project.id)
         assert data['type'] == 'projects'

         attributes = data['attributes']
         assert 'actual' in attributes
         assert 'buffer' in attributes
         assert 'estimated' in attributes
         assert 'name' in attributes
         assert attributes['actual'] > 60
         assert attributes['buffer'] == 0
         assert attributes['estimated'] == 85
         assert attributes['name'] == self.project.name
