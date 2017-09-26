from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django_cron import CronJobBase, Schedule
from django.utils import timezone
from python_http_client.exceptions import BadRequestsError

from authentication.models import UserProfile


class TrailExpirationCronJob(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'albatross_api.cron.TrailExpirationCronJob'

    def send_email(self, email, name, type):
        if type == 'almost_expired':
            subject = "Your Free Trail is Almost Over - Upgrade Now"
            template_id = "f34b927e-2fc3-4761-85b3-eeb319307cd0"
        if type == 'expired':
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
        profiles_with_almost_expired_trials = UserProfile.objects.filter(
            on_trial = True,
            trial_expires_at__gte = timezone.now(),
            trial_expires_at__lte = timezone.now() + timedelta(days=3)
        )
        for profile in profiles_with_almost_expired_trials:
            self.send_email(profile.user.email,
                            profile.user.first_name,
                            'almost_expired')

        profiles_with_expired_trials = UserProfile.objects.filter(
            on_trial = True,
            trial_expires_at__lte = timezone.now()
        )
        for profile in profiles_with_expired_trials:
            profile.on_trial = False
            profile.save()
            self.send_email(profile.user.email,
                            profile.user.first_name,
                            'expired')
