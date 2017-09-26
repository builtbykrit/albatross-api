from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .cron import TrailExpirationCronJob


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

        user_with_nearly_expired_trial = User.objects.create_user(
            email='user.2@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.2@example.com'
        )
        profile = user_with_nearly_expired_trial.profile
        profile.trial_expires_at = timezone.now() + timedelta(hours=71)
        profile.save()

        user_with_expired_trial = User.objects.create_user(
            email='user.3@example.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='user.3@example.com'
        )
        profile = user_with_expired_trial.profile
        profile.trial_expires_at = timezone.now() - timedelta(hours=1)
        profile.save()

        # Run cronjob
        cronjob = TrailExpirationCronJob()
        cronjob.do()

        # Verify results
        user = User.objects.get(id=user.id)
        profile = user.profile
        assert profile.on_trial == True
        assert profile.trial_expires_at > timezone.now() + timedelta(days=13)

        user_with_nearly_expired_trial = User.objects.get(
            id=user_with_nearly_expired_trial.id)
        profile = user_with_nearly_expired_trial.profile
        assert profile.on_trial == True

        user_with_expired_trial = User.objects.get(
            id=user_with_expired_trial.id)
        profile = user_with_expired_trial.profile
        assert profile.on_trial == False
