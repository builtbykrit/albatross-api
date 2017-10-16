from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime

UserModel = get_user_model()


class UserProfile(models.Model):
    """
    A model to store a user's settings
    """
    beta = models.BooleanField(default=True)
    harvest_access_token = models.CharField(max_length=200, blank=True)
    harvest_refresh_token = models.CharField(max_length=200, blank=True)
    harvest_tokens_last_refreshed_at = models.CharField(max_length=200, blank=True,
                                                            null=True)
    toggl_api_key = models.CharField(max_length=200, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='profile',
        on_delete=models.CASCADE, verbose_name="User",
        primary_key=True
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    class JSONAPIMeta:
        resource_name = "profiles"

    def __setattr__(self, attrname, val):
        super(UserProfile, self).__setattr__(attrname, val)
        if (attrname == 'harvest_access_token'
            or attrname == 'harvest_refresh_token'):
            super(UserProfile, self).__setattr__(
                'harvest_tokens_last_refreshed_at',
                str(datetime.datetime.now())
            )

@receiver(post_save, sender=UserModel)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserModel)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()