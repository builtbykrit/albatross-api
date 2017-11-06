from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from django.contrib.auth.models import User
from django.test import TestCase
from projects.models import Category, Item, Project
from teams.models import Team

from .hooks import hookset


class HarvestTestCase(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )

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
        # Create one category with the correct name but incorrect
        # casing so that we can make sure our integration ignores case
        category = Category.objects.create(
            name='back end dev',
            project=self.project
        )
        items = [('authentication',10),
                 ('Categories',8),
                 ('Deployment',25),
                 ('Line Items',8),
                 ('Projects',6),
                 ('Settings',3),
                 ('Signup',2.5),
                 ('Summary',3),
                 ('Teams',6),
                 ('Toggl integration',6),
                 ('Users',5),
                 ('Invitations',2.5)]
        for item in items:
            Item.objects.create(
                actual=0,
                category=category,
                description=item[0],
                estimated=item[1]
            )
        # Create another category
        category = Category.objects.create(
            name='Design',
            project=self.project
        )
        items = [('API Token',3),
                 ('Authentication',3),
                 ('Base Styles',4),
                 ('Project',8),
                 ('Projects',5),
                 ('Prototyping',2),
                 ('Settings',2),
                 ('Users',2)]
        for item in items:
            Item.objects.create(
                actual=0,
                category=category,
                description=item[0],
                estimated=item[1]
            )

    def test_import_project_data_from_harvest(self):
        # We have to unit test our hook method instead of using
        # an integration test because the personal token we're
        # using to test with requires an account id to be included
        # in the request.
        harvest_credentials = {
            'account_id': '467159',
            'access_token': '31907.pt.pgATDbOm81BpPa1zR9EbeJz_FaklVfx7dIU1v0O2FaOYWriEyuTjvzb7aEHnrO44-AjiFat_2o7aMICgygiwhg'
        }
        hookset.update_project_line_item_times(
            self=hookset,
            api_credentials=harvest_credentials,
            project_to_update=self.project
        )

        updated_project = Project.objects.get(id=self.project.id)
        assert updated_project.actual > Decimal(19.5) # design is only thing in harvest

        assert (updated_project.last_imported_date - timezone.now() < timedelta(seconds=15))
