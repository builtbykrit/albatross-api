import mock
import unittest
from mock import MagicMock

from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from harvest.utils import TokensManager
from authentication.models import UserProfile

from teams.models import Team
from projects.models import Project, Category, Item

from .cron import RefreshHarvestTokensCronJob, TrailExpirationCronJob, ImportHoursCronJob, WeeklyProgressCronJob


class RefreshHarvestTokensCronJobTestCase(TestCase):
    def test_case_where_no_user_has_harvest_credentials(self):
        user = User.objects.create_user(
            email='user.1@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.1@example.com'
        )
        Team.objects.create(
            creator=user,
            name="Team"
        )

        cronjob = RefreshHarvestTokensCronJob()
        cronjob.do()

    @mock.patch('harvest.utils.TokensManager')
    def test_case_where_user_has_invalid_harvest_credentials(self, mock_token_manager):
        user = User.objects.create_user(
            email='user.2@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.2@example.com'
        )

        user.profile.harvest_access_token = "123"
        user.profile.harvest_refresh_token = "456"
        user.profile.harvest_tokens_last_refreshed_at = "2017-10-01 15:51:32.311970"
        user.save()
        Team.objects.create(
            creator=user,
            name="Team"
        )
        mock_token_manager.refresh_access_token_by_demand.return_value = None
        mock_token_manager.is_access_token_fresh.return_value = False

        cronjob = RefreshHarvestTokensCronJob()
        cronjob.do()

        user_profile = UserProfile.objects.get(user=user)

        self.assertEqual(user_profile.harvest_access_token, "")
        self.assertEqual(user_profile.harvest_refresh_token, "")
        self.assertEqual(user_profile.harvest_tokens_last_refreshed_at, None)

class TrailExpirationCronJobTestCase(TestCase):
    ACCOUNT_CREDENTIALS = {
        'email': 'bill@builtbykrit.com',
        'password': 'password125'
    }

    def create_user(self, account_credentials):
        User.objects.create_user(
            email=account_credentials['email'],
            first_name='Test',
            last_name='Account',
            password=account_credentials['password'],
            username=account_credentials['email']
        )

    def test_cronjob(self):
        # Setup users
        user = User.objects.create_user(
            email='user.1@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.1@example.com'
        )
        team = Team.objects.create(
            creator=user,
            name="Team"
        )

        user_with_nearly_expired_trial = User.objects.create_user(
            email='user.2@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.2@example.com'
        )
        team_with_nearly_expired_trial = Team.objects.create(
            creator=user_with_nearly_expired_trial,
            name="Team with nearly expired trial",
            trial_expires_at=timezone.now() + timedelta(hours=71)
        )

        user_with_expired_trial = User.objects.create_user(
            email='user.3@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.3@example.com'
        )
        team_with_expired_trial = Team.objects.create(
            creator=user_with_nearly_expired_trial,
            name="Team with expired trial",
            trial_expires_at=timezone.now() - timedelta(hours=1)
        )

        # Run cronjob
        cronjob = TrailExpirationCronJob()
        cronjob.do()

        # Verify results
        team = Team.objects.get(id=team.id)
        assert team.on_trial == True
        assert team.trial_expires_at > timezone.now() + timedelta(days=13)

        team_with_nearly_expired_trial = Team.objects.get(
            id=team_with_nearly_expired_trial.id)
        assert team_with_nearly_expired_trial.on_trial == True

        team_with_expired_trial = Team.objects.get(
            id=team_with_expired_trial.id)
        assert team_with_expired_trial.on_trial == False


class ImportHoursCronJobTestCase(TestCase):
    def test_case_where_no_user_has_toggl_harvest_credentials(self):
        user = User.objects.create_user(
            email='user.3@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.3@example.com'
        )
        Team.objects.create(
            creator=user,
            name="Team"
        )

        cronjob = ImportHoursCronJob()
        cronjob.do()

class WeeklyProgressCronJobTestCase(TestCase):
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
        project = Project.objects.create(name=self.PROJECT_NAME, team=team)
        category = Category.objects.create(name=self.CATEGORY_NAME, project=project)
        Item.objects.create(description=self.ITEM_DESCRIPTION, actual=5, estimated=20, category=category)

    def test_weekly_hours(self):
        cronjob = WeeklyProgressCronJob()
        project = Project.objects.get(name=self.PROJECT_NAME)
        hours = cronjob.get_project_weekly_hours(project)

        self.assertEqual(hours, 5)
        self.assertEqual(project.actual, project.last_weeks_hours)

    def test_get_projects_data(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters', creator=user)
        project = Project.objects.create(name='Project', team=team, last_weeks_hours=6)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=12, estimated=25, category=category)

        cronjob = WeeklyProgressCronJob()
        projects_data = cronjob.get_projects_data_for_user(user)

        self.assertIn({"weekly_hours", 6}, projects_data)
        self.assertIn({"weekly_hours", 5}, projects_data)

