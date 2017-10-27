from datetime import timedelta
from datetime import date
import itertools
from authentication.models import UserProfile
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from harvest.hooks import hookset as harvest_hookset
from harvest.utils import TokensManager
from python_http_client.exceptions import BadRequestsError
from teams.models import Team, Membership
from toggl.hooks import hookset as toggl_hookset
from django.db import transaction

from enum import Enum

UserModel = get_user_model()


class RefreshHarvestTokensCronJob(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'albatross_api.cron.RefreshHarvestTokensCronJob'

    def do(self):
        harvest_users = UserProfile.objects.filter(
            ~Q(harvest_access_token='')
        )
        for user in harvest_users:
            token_manager = TokensManager(
                access_token=user.harvest_access_token,
                client_id=settings.HARVEST_CLIENT_ID,
                client_secret=settings.HARVEST_CLIENT_SECRET,
                refresh_token=user.harvest_refresh_token,
                tokens_last_refreshed_at=user.harvest_tokens_last_refreshed_at)
            new_tokens = token_manager.refresh_access_token_by_demand()
            if new_tokens:
                user.harvest_access_token = new_tokens['access_token']['value']
                user.harvest_refresh_token = new_tokens['refresh_token']['value']
                user.harvest_tokens_last_refreshed_at = new_tokens['refresh_token'][token_manager.last_refresh_time_key]
                user.save()
            else:
                # If new tokens were not obtained and the access token is not fresh, then the user needs to
                # reauthenticate
                if not token_manager.is_access_token_fresh():
                    user.harvest_access_token = ""
                    user.harvest_refresh_token = ""
                    user.harvest_tokens_last_refreshed_at = None
                    user.save()


class TrailExpirationCronJob(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'albatross_api.cron.TrailExpirationCronJob'

    @staticmethod
    def send_email(email, name, notification_type):
        if notification_type == 'almost_expired':
            subject = "Your Free Trail is Almost Over - Upgrade Now"
            template_id = "f34b927e-2fc3-4761-85b3-eeb319307cd0"
        if notification_type == 'expired':
            subject = "Your Free Trail Just Expired - Upgrade Now"
            template_id = "2defda40-48e1-4247-b1b4-aaa265918cc5"

        mail = EmailMultiAlternatives(
            subject=subject,
            body="test",
            from_email="Andrew Askins <andrew@builtbykrit.com>",
            reply_to=["andrew@builtbykrit.com>"],
            to=[email]
        )
        mail.substitutions = {'%name%': name}
        mail.template_id = template_id

        # So Sendgrid sends the html version of the template instead of text
        mail.attach_alternative('test', "text/html")
        try:
            mail.send()
        except BadRequestsError as e:
            print(e.reason)
            raise e

    def do(self):
        teams_with_almost_expired_trials = Team.objects.filter(
            on_trial=True,
            trial_expires_at__gte=timezone.now(),
            trial_expires_at__lte=timezone.now() + timedelta(days=3)
        )
        for team in teams_with_almost_expired_trials:
            key = 'team_{}:trail_almost_expired'.format(team.id)
            if cache.get(key):
                continue
            self.send_email(team.creator.email,
                            team.creator.first_name,
                            'almost_expired')
            cache.set(key, 'almost_expired', 60 * 60 * 24 * 3)

        teams_with_expired_trials = Team.objects.filter(
            on_trial=True,
            trial_expires_at__lte=timezone.now()
        )
        for team in teams_with_expired_trials:
            team.on_trial = False
            team.save()
            self.send_email(team.creator.email,
                            team.creator.first_name,
                            'expired')


class ImportHoursCronJob(CronJobBase):
    RUN_AT_TIMES = ['05:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)

    code = 'albatross_api.cron.ImportHoursCronJob'

    @staticmethod
    def update_projects(user, api_key, hookset):
        try:
            membership = Membership.objects.get(user=user)
            projects = membership.team.projects.all()
            for project in projects:
                project.update_actual(api_key, hookset)
        except Membership.DoesNotExist as e:
            pass

    def do(self):
        harvest_users = UserProfile.objects.filter(
            ~Q(harvest_access_token='')
        )

        for user_profile in harvest_users:
            tokens = {
                'access_token': user_profile.harvest_access_token,
                'refresh_token': user_profile.harvest_refresh_token,
                'tokens_last_refreshed_at': user_profile.harvest_tokens_last_refreshed_at
            }
            print(tokens)

            self.update_projects(user_profile.user, tokens, harvest_hookset)

        toggl_users = UserProfile.objects.filter(
            ~Q(toggl_api_key='')
        )

        for user_profile in toggl_users:
            api_key = user_profile.toggl_api_key

            self.update_projects(user_profile.user, api_key, toggl_hookset)


class WeeklyProgressCronJob(CronJobBase):
    RUN_AT_TIMES = ['06:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)

    code = 'albatross_api.cron.WeeklyProgressCronJob'

    class Status(Enum):
        OVER = 1
        CLOSE = 2
        UNDER = 3

    def get_status(self, estimated, actual):
        hours_diff = estimated - actual
        if hours_diff < 0:
            return self.Status.OVER
        elif hours_diff < estimated * Decimal(.1):
            return self.Status.CLOSE
        else:
            return self.Status.UNDER

    @staticmethod
    def get_project_weekly_hours(project):
        hours_diff = project.actual - project.last_weeks_hours
        weekly_hours = hours_diff if hours_diff > 0 else 0
        project.last_weeks_hours = project.actual

        # Store last weeks hours into previous weeks hours
        previous_weeks_hours = project.previous_weeks_hours
        if previous_weeks_hours is None:
            previous_weeks_hours = []

        previous_weeks_hours.insert(0, [weekly_hours, timezone.now().strftime('%B %d')])
        project.previous_weeks_hours = previous_weeks_hours
        project.save()

        return previous_weeks_hours

    @staticmethod
    def get_team_weekly_hours(projects_data):
        projects_previous_hours = []
        for project_data in projects_data:
            previous_weeks_hours = project_data['previous_weeks_hours']
            project_hours = []
            for hours in previous_weeks_hours:
                project_hours.append(hours[0])
            projects_previous_hours.append(project_hours)
        return [sum(x) for x in itertools.zip_longest(*projects_previous_hours, fillvalue=0)]


    @transaction.atomic
    def get_projects_data_for_user(self, user):
        try:
            membership = Membership.objects.get(user=user)
            projects = membership.team.projects.all()
            projects_data = []
            for project in projects:
                project_data = {}

                project_data["previous_weeks_hours"] = self.get_project_weekly_hours(project)
                project_data["name"] = project.name

                estimated = project.estimated
                actual = project.actual

                project_data["estimated"] = estimated
                project_data["actual"] = actual
                project_data["hours_diff"] = estimated - actual
                project_data["status"] = self.get_status(estimated=estimated, actual=actual)
                project_data["id"] = project.id

                items_under = 0
                items_close = 0
                items_over = 0
                for category in project.categories.all():
                    for item in category.items.all():
                        item_status = self.get_status(estimated=item.estimated, actual=item.actual)
                        if item_status is self.Status.UNDER:
                            items_under += 1
                        elif item_status is self.Status.CLOSE:
                            items_close += 1
                        else:
                            items_over += 1

                project_data["items_under"] = items_under
                project_data["items_close"] = items_close
                project_data["items_over"] = items_over

                projects_data.append(project_data)

            return projects_data
        except Membership.DoesNotExist:
            pass

    def do(self):
        # if date.today().weekday() != 0:
        #    return
        users = UserModel.objects.all()

        report_start = date.today() - timedelta(days=7)
        report_end = date.today()

        date_range = '%s - %s' % (report_start.strftime('%B %d'), report_end.strftime('%B %d'))

        for user in users:
            projects_data = self.get_projects_data_for_user(user)
            user_first_name = user.first_name

            team_previous_hours = self.get_team_weekly_hours(projects_data)
            # If the team has not tracked any hours this week, dont send an email
            if team_previous_hours[0] == 0:
                continue
