import itertools
import os
from datetime import date
from datetime import timedelta
from decimal import Decimal
from enum import Enum
import re

from authentication.models import UserProfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from harvest.hooks import hookset as harvest_hookset
from harvest.utils import TokensManager
from python_http_client.exceptions import BadRequestsError
from teams.models import Team, Membership
from toggl.hooks import hookset as toggl_hookset

from projects.models import Project

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
        template = ""
        if notification_type == 'almost_expired':
            subject = "Your Free Trial is Almost Over - Upgrade Now"
            template = "trial-almost-expired"
        if notification_type == 'expired':
            subject = "Your Free Trial Just Expired - Upgrade Now"
            template = "trial-expired"

        mail = EmailMultiAlternatives(
            subject=subject,
            body="test",
            from_email="Andrew Askins <andrew@builtbykrit.com>",
            reply_to=["andrew@builtbykrit.com>"],
            to=[email]
        )
        mail.substitution_data = {'name': name,
                                  'subject': subject}
        mail.template = template

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


def format_decimal(num):
    return str(round(num, 2) if num % 1 else int(num))


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
    def update_project_weekly_hours(project):
        hours_diff = project.actual - project.last_weeks_hours
        weekly_hours = hours_diff if hours_diff > 0 else 0
        project.last_weeks_hours = project.actual

        # Store last weeks hours into previous weeks hours
        previous_weeks_hours = project.previous_weeks_hours
        if previous_weeks_hours is None:
            previous_weeks_hours = []

        previous_weeks_hours.insert(0, [weekly_hours, timezone.now().strftime('%b %d')])
        project.previous_weeks_hours = previous_weeks_hours
        project.save()

        return previous_weeks_hours

    @staticmethod
    def get_team_weekly_hours(projects_data):
        projects_previous_hours = []
        projects_previous_dates = []

        for project_data in projects_data:
            previous_weeks_hours = project_data['previous_weeks_hours']
            project_hours = []
            for hours in previous_weeks_hours:
                project_hours.append(hours[0])
                if hours[1] not in projects_previous_dates:
                    projects_previous_dates.append(hours[1])
            projects_previous_hours.append(project_hours)

        return [sum(x) for x in itertools.zip_longest(*projects_previous_hours, fillvalue=0)], projects_previous_dates

    @transaction.atomic
    def get_projects_data_for_user(self, user):
        try:
            membership = Membership.objects.get(user=user)
            # Only show active projects in the report
            projects = membership.team.projects.filter(archived=False)
            projects_data = []
            for project in projects:
                project_data = {}

                project_data["previous_weeks_hours"] = project.previous_weeks_hours
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

                project_data["items_under"] = '{} item{} under'.format(items_under, '' if items_under == 1 else 's')
                project_data["items_close"] = '{} item{} close'.format(items_close, '' if items_close == 1 else 's')
                project_data["items_over"] = '{} item{} over'.format(items_over, '' if items_over == 1 else 's')

                projects_data.append(project_data)

            return projects_data
        except Membership.DoesNotExist:
            pass

    def generate_weekly_history_substitutions(self, previous_weeks_hours):
        weekly_history_substitutions = []
        previous_hours = previous_weeks_hours[0][:4]
        previous_dates = previous_weeks_hours[1][:4]

        if len(previous_hours) == 0:
            return weekly_history_substitutions
        max_hours = max(previous_hours)
        if max_hours == 0:
            return weekly_history_substitutions
        for hours, date in itertools.zip_longest(previous_hours, previous_dates, fillvalue=None):
            height = "{0:.0f}%".format(hours / max_hours * 100)
            if date is None: date = previous_dates[0]
            substitutions = {
                'height': height,
                'date': date,
            }
            weekly_history_substitutions.append(substitutions)

        return weekly_history_substitutions

    def generate_projects_substitutions(self, projects_data):
        projects_substitutions = []

        for project_data in projects_data:
            actual = project_data["actual"]
            formatted_actual = format_decimal(actual)

            estimated = project_data["estimated"]
            formatted_estimated = format_decimal(estimated)

            status = project_data["status"]
            hours_diff = format_decimal(abs(project_data["hours_diff"]))

            color = ""
            color_hex = ""
            status_text = ""

            pluralize_hours = int(hours_diff) != 1
            if status is self.Status.OVER:
                color = "red"
                color_hex = "#F46070"
                status_text = "{} hour{} over".format(hours_diff, 's' if pluralize_hours else '')
            elif status is self.Status.CLOSE:
                color = "yellow"
                color_hex = "#FDD371"
                status_text = "{} hour{} under".format(hours_diff, 's' if pluralize_hours else '')
            elif status is self.Status.UNDER:
                color = "green"
                color_hex = "#56D694"
                status_text = "{} hour{} under".format(hours_diff, 's' if pluralize_hours else '')

            substitutions = {
                'name': project_data['name'],
                'actual': formatted_actual,
                'estimated': formatted_estimated,
                'color': color,
                'color_hex': color_hex,
                'status': status_text,
                'id': str(project_data["id"]),
                'items_under': project_data['items_under'],
                'items_close': project_data['items_close'],
                'items_over': project_data['items_over']

            }

            projects_substitutions.append(substitutions)

        return projects_substitutions

    @staticmethod
    def send_email(email, name, date, total_hours, history, projects):
        template = "weekly-report"

        mail = EmailMultiAlternatives(
            subject="Weekly Report",
            from_email="Andrew Askins <andrew@builtbykrit.com>",
            reply_to=["andrew@builtbykrit.com>"],
            to=[email]
        )
        mail.substitution_data = {'name': name,
                                  'date_range': date,
                                  'total_hours': total_hours,
                                  'history': history,
                                  'projects': projects}
        mail.template = template

        try:
            mail.send()
        except BadRequestsError as e:
            print(e.body)
            raise e

    def update_all_projects(self):
        projects = Project.objects.all()
        for project in projects:
            self.update_project_weekly_hours(project)

    def do(self):
        # TODO: Uncomment before deploying
        # if date.today().weekday() != 0:
        #    return
        users = UserModel.objects.all()

        report_start = date.today() - timedelta(days=7)
        report_end = date.today()

        date_range = '%s - %s' % (report_start.strftime('%B %d'), report_end.strftime('%B %d'))

        self.update_all_projects()
        for user in users:
            projects_data = self.get_projects_data_for_user(user)
            name = user.first_name
            email = user.email

            team_previous_hours = self.get_team_weekly_hours(projects_data)
            total_hours = format_decimal(team_previous_hours[0][0])
            # If the team has not tracked any hours this week, dont send an email
            if total_hours == 0:
                continue

            history = self.generate_weekly_history_substitutions(team_previous_hours)
            projects_substitutions = self.generate_projects_substitutions(projects_data)

            self.send_email(email=email,
                            name=name,
                            date=date_range,
                            total_hours=total_hours,
                            history=history,
                            projects=projects_substitutions)
