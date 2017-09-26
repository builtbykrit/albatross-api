from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

def fourteen_days_ahead():
    return timezone.now() + timedelta(days=14)


UserModel = get_user_model()


class UserProfile(models.Model):
    """
    A model to store a user's Toggl related settings
    """
    beta = models.BooleanField(default=True)
    on_trial = models.BooleanField(default=True)
    toggl_api_key = models.CharField(max_length=200, blank=True)
    trial_expires_at = models.DateTimeField(default=fourteen_days_ahead)
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

@receiver(post_save, sender=UserModel)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserModel)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()