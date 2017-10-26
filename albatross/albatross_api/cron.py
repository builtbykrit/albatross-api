import mock

from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django_cron import CronJobBase, Schedule
from django.db.models import Q
from django.utils import timezone
from python_http_client.exceptions import BadRequestsError

from authentication.models import UserProfile
from harvest.utils import TokensManager
from teams.models import Team, Membership
from harvest.hooks import hookset as harvest_hookset
from toggl.hooks import hookset as toggl_hookset


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
