import mock
import unittest

from decimal import Decimal
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
            name='Team'
        )

        cronjob = RefreshHarvestTokensCronJob()
        cronjob.do()

    @mock.patch('harvest.utils.TokensManager.refresh_access_token_by_demand')
    @mock.patch('harvest.utils.TokensManager.is_access_token_fresh')
    def test_case_where_user_has_invalid_harvest_credentials(self, mock_refresh_access_token_by_demand,
                                                             mock_is_access_token_fresh):
        user = User.objects.create_user(
            email='user.2@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.2@example.com'
        )

        user.profile.harvest_access_token = '123'
        user.profile.harvest_refresh_token = '456'
        user.profile.harvest_tokens_last_refreshed_at = '2017-10-01 15:51:32.311970'
        user.save()
        Team.objects.create(
            creator=user,
            name='Team'
        )
        mock_refresh_access_token_by_demand.return_value = None
        mock_is_access_token_fresh.return_value = False

        cronjob = RefreshHarvestTokensCronJob()
        cronjob.do()

        user_profile = UserProfile.objects.get(user=user)

        self.assertEqual(user_profile.harvest_access_token, '')
        self.assertEqual(user_profile.harvest_refresh_token, '')
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
            name='Team',
            on_trial=True

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
            name='Team with nearly expired trial',
            on_trial=True,
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
            name='Team with expired trial',
            on_trial=True,
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
            name='Team'
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
        Item.objects.create(description='Another item', actual=25, estimated=20, category=category)
        Item.objects.create(description='Yet Another', actual=19, estimated=20, category=category)

    def test_weekly_hours(self):
        cronjob = WeeklyProgressCronJob()
        project = Project.objects.get(name=self.PROJECT_NAME)
        hours = cronjob.update_project_weekly_hours(project)

        self.assertEqual(hours[0], [Decimal(49), timezone.now().strftime('%b %d')])
        self.assertEqual(project.actual, project.last_weeks_hours)

    def test_generate_projects_substitutions(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters', creator=user)
        project = Project.objects.create(name='Project', team=team, last_weeks_hours=6)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=24, estimated=25, category=category)

        over_project = Project.objects.create(name='Over Project', team=team)
        over_category = Category.objects.create(name='New Category', project=over_project)
        Item.objects.create(description='Testing', actual=36, estimated=29, category=over_category)
        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()

        projects_data = cronjob.get_projects_data_for_user(user)
        substitutions = cronjob.generate_projects_substitutions(projects_data)

        over_project_substitutions = substitutions[0]
        self.assertEqual("Over Project", over_project_substitutions['name'])
        self.assertEqual('29', over_project_substitutions['estimated'])
        self.assertEqual('36', over_project_substitutions['actual'])
        self.assertEqual('red', over_project_substitutions['color'])
        self.assertEqual('#F46070', over_project_substitutions['color_hex'])
        self.assertEqual('0 items under', over_project_substitutions['items_under'])
        self.assertEqual('1 item over', over_project_substitutions['items_over'])
        self.assertEqual('0 items close', over_project_substitutions['items_close'])

        project_substitutions = substitutions[1]
        self.assertEqual('Project', project_substitutions['name'])
        self.assertEqual('25', project_substitutions['estimated'])
        self.assertEqual('24', project_substitutions['actual'])
        self.assertEqual('yellow', project_substitutions['color'])
        self.assertEqual('#FDD371', project_substitutions['color_hex'])
        self.assertEqual('0 items under', project_substitutions['items_under'])
        self.assertEqual('0 items over', project_substitutions['items_over'])
        self.assertEqual('1 item close', project_substitutions['items_close'])

        my_project_substitutions = substitutions[2]
        self.assertEqual(self.PROJECT_NAME, my_project_substitutions['name'])
        self.assertEqual('60', my_project_substitutions['estimated'])
        self.assertEqual('49', my_project_substitutions['actual'])
        self.assertEqual('green', my_project_substitutions['color'])
        self.assertEqual('#56D694', my_project_substitutions['color_hex'])
        self.assertEqual('1 item under', my_project_substitutions['items_under'])
        self.assertEqual('1 item over', my_project_substitutions['items_over'])
        self.assertEqual('1 item close', my_project_substitutions['items_close'])

    def test_generate_weekly_substitutions(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        category = Category.objects.get(name=self.CATEGORY_NAME)
        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()

        cronjob.get_projects_data_for_user(user=user)

        item = Item.objects.create(description='New Item', actual=11, estimated=25, category=category)
        item.save()

        projects_data = cronjob.get_projects_data_for_user(user=user)

        previous_hours = cronjob.get_team_weekly_hours(projects_data)
        previous_hours[0].insert(1, 13)
        previous_hours[1].insert(1, 'Dec 10')
        substitutions = cronjob.generate_weekly_history_substitutions(previous_hours)
        current_week_substitutions = substitutions[0]
        self.assertEqual('100%', current_week_substitutions['height'])
        self.assertEqual(timezone.now().strftime('%b %d'), current_week_substitutions['date'])

        last_week_substitutions = substitutions[1]
        self.assertEqual('27%', last_week_substitutions['height'])
        self.assertEqual("Dec 10", last_week_substitutions['date'])

    def test_generate_weekly_substitutions_empty(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        project = Project.objects.get(name=self.PROJECT_NAME)
        project.last_weeks_hours = 49
        project.save()

        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()
        projects_data = cronjob.get_projects_data_for_user(user=user)
        previous_hours = cronjob.get_team_weekly_hours(projects_data)
        weekly_history_substitutions = cronjob.generate_weekly_history_substitutions(previous_hours)
        self.assertEqual(weekly_history_substitutions, [])

    def test_get_projects_data(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters', creator=user)
        project = Project.objects.create(name='Project', team=team, last_weeks_hours=6)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=24, estimated=25, category=category)

        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()
        projects_data = cronjob.get_projects_data_for_user(user)

        first_project_index = 0 if projects_data[0]['name'] == self.PROJECT_NAME else 1
        second_project_index = 0 if first_project_index == 1 else 1

        self.assertEquals(projects_data[first_project_index]['estimated'], 60)
        self.assertEquals(projects_data[first_project_index]['actual'], 49)
        self.assertEquals(projects_data[first_project_index]['hours_diff'], 11)
        self.assertEquals(projects_data[first_project_index]['name'], self.PROJECT_NAME)
        self.assertEquals(projects_data[first_project_index]['status'], cronjob.Status.UNDER)
        self.assertEquals(projects_data[first_project_index]['id'], Project.objects.get(name=self.PROJECT_NAME).id)
        self.assertEquals(projects_data[first_project_index]['items_under'], '1 item under')
        self.assertEquals(projects_data[first_project_index]['items_close'], '1 item close')
        self.assertEquals(projects_data[first_project_index]['items_over'], '1 item over')

        self.assertEquals(projects_data[second_project_index]['estimated'], 25)
        self.assertEquals(projects_data[second_project_index]['actual'], 24)
        self.assertEquals(projects_data[second_project_index]['hours_diff'], 1)
        self.assertEquals(projects_data[second_project_index]['name'], 'Project')
        self.assertEquals(projects_data[second_project_index]['status'], cronjob.Status.CLOSE)
        self.assertEquals(projects_data[second_project_index]['id'], project.id)
        self.assertEquals(projects_data[second_project_index]['items_under'], '0 items under')
        self.assertEquals(projects_data[second_project_index]['items_close'], '1 item close')
        self.assertEquals(projects_data[second_project_index]['items_over'], '0 items over')

    def test_get_team_data(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters', creator=user)
        project = Project.objects.create(name='Project', team=team)
        category = Category.objects.create(name='Category', project=project)
        item = Item.objects.create(description='Item', actual=24, estimated=25, category=category)

        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()
        projects_data = cronjob.get_projects_data_for_user(user)
        team_previous_hours = cronjob.get_team_weekly_hours(projects_data)

        self.assertEqual(team_previous_hours, ([73], [timezone.now().strftime('%b %d')]))

        Item.objects.create(description='New Item', actual=11, estimated=25, category=category)
        item.actual = 35
        item.save()

        cronjob.update_all_projects()
        new_projects_data = cronjob.get_projects_data_for_user(user)
        new_team_previous_hours = cronjob.get_team_weekly_hours(new_projects_data)

        self.assertEqual(new_team_previous_hours, ([22, 73], [timezone.now().strftime('%b %d')]))

        project = Project.objects.create(name='Another Project', team=team)
        new_category = Category.objects.create(name='Another Category', project=project)
        Item.objects.create(description='Another Item', actual=3, estimated=30, category=new_category)

        item.actual = 40
        item.save()

        Category.objects.create(name='New category', project=project)
        Item.objects.create(description='Third Item', actual=3, estimated=25, category=category)

        cronjob.update_all_projects()
        third_projects_data = cronjob.get_projects_data_for_user(user)
        third_team_previous_hours = cronjob.get_team_weekly_hours(third_projects_data)
        self.assertEqual(third_team_previous_hours, ([11, 22, 73], [timezone.now().strftime('%b %d')]))


    @mock.patch('albatross_api.cron.WeeklyProgressCronJob.send_email')
    @mock.patch('albatross_api.cron.WeeklyProgressCronJob.is_monday')
    def test_wants_weekly_emails_false(self, mock_is_monday, mock_send_email):
        mock_is_monday.return_value = True
        mock_send_email.return_value = True

        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters')
        project = Project.objects.create(name='Project', team=team)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=24, estimated=25, category=category)

        profiles = UserProfile.objects.all()
        for profile in profiles:
            profile.wants_weekly_emails = False
            profile.save()

        cronjob = WeeklyProgressCronJob()
        cronjob.do()

        self.assertEqual(mock_send_email.call_count, 0)

    def test_generate_weekly_substitutions_decimal_hours(self):
        user = User.objects.get(email='kehoffman3@gmail.com')
        team = Team.objects.get(name='Kritters', creator=user)
        project = Project.objects.create(name='Project', team=team, last_weeks_hours=6)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=24.31, estimated=25, category=category)

        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()

        projects_data = cronjob.get_projects_data_for_user(user)
        substitutions = cronjob.generate_projects_substitutions(projects_data)

        project_substitutions = substitutions[0]
        self.assertEqual('Project', project_substitutions['name'])
        self.assertEqual('25', project_substitutions['estimated'])
        self.assertEqual('24.31', project_substitutions['actual'])
        self.assertEqual('yellow', project_substitutions['color'])
        self.assertEqual('#FDD371', project_substitutions['color_hex'])
        self.assertEqual('0.69 hours under', project_substitutions['status'])
        self.assertEqual(str(project.id), project_substitutions['id'])
        self.assertEqual('0 items under', project_substitutions['items_under'])
        self.assertEqual('0 items over', project_substitutions['items_over'])
        self.assertEqual('1 item close', project_substitutions['items_close'])

        my_project_substitutions = substitutions[1]
        self.assertEqual(self.PROJECT_NAME, my_project_substitutions['name'])
        self.assertEqual('60', my_project_substitutions['estimated'])
        self.assertEqual('49', my_project_substitutions['actual'])
        self.assertEqual('11 hours under', my_project_substitutions['status'])
        self.assertEqual('green', my_project_substitutions['color'])
        self.assertEqual('#56D694', my_project_substitutions['color_hex'])
        self.assertEqual('1 item under', my_project_substitutions['items_under'])
        self.assertEqual('1 item over', my_project_substitutions['items_over'])
        self.assertEqual('1 item close', my_project_substitutions['items_close'])

    @mock.patch('albatross_api.cron.WeeklyProgressCronJob.send_email')
    @mock.patch('albatross_api.cron.WeeklyProgressCronJob.is_monday')
    def test_archived_projects_not_shown(self, mock_is_monday, mock_send_email):
        mock_is_monday.return_value = True
        mock_send_email.return_value = True

        user = User.objects.create_user(
            email='user.10@example.com',
            first_name='Test',
            last_name='Account',
            username='user.10@example.com'
        )
        team = Team.objects.create(
            creator=user,
            name='Team'
        )
        project = Project.objects.create(name='Project', team=team)
        category = Category.objects.create(name='Category', project=project)
        Item.objects.create(description='Item', actual=24, estimated=25, category=category)

        project_archived = Project.objects.create(name='Project Archived', team=team, archived=True)
        category_archived = Category.objects.create(name='Category Archived', project=project_archived)
        Item.objects.create(description='Item', actual=5, estimated=25, category=category_archived)

        cronjob = WeeklyProgressCronJob()
        cronjob.update_all_projects()

        projects_data = cronjob.get_projects_data_for_user(user)
        substitutions = cronjob.generate_projects_substitutions(projects_data)

        team_previous_hours = cronjob.get_team_weekly_hours(projects_data)
        self.assertEqual(team_previous_hours[0][0], 29)

        project_substitutions = substitutions[0]
        self.assertEqual(len(substitutions), 1)
        self.assertEqual('Project', project_substitutions['name'])
        self.assertEqual('25', project_substitutions['estimated'])
        self.assertEqual('24', project_substitutions['actual'])





