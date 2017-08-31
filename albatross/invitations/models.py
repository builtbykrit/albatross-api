from django.db import models
from django.utils import timezone
from registration.models import SignupCode

from .conf import settings
from .signals import invite_accepted, invite_sent


class Invitation(models.Model):

    STATUS_SENT = 1
    STATUS_ACCEPTED = 2

    INVITE_STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_ACCEPTED, "Accepted"),
    ]

    from_user = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name="invites_sent")
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="invites_received"
    )
    message = models.TextField(null=True)
    sent = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=INVITE_STATUS_CHOICES)
    signup_code = models.OneToOneField(SignupCode)

    def to_user_email(self):
        return self.signup_code.email

    def accept(self, user):
        self.to_user = user
        self.status = Invitation.STATUS_ACCEPTED
        self.save()
        invite_accepted.send(sender=Invitation, invitation=self)

    @classmethod
    def invite(cls, from_user, to_email, message=None, send=True):
        signup_code = SignupCode.create(
            email=to_email,
            inviter=from_user,
            check_exists=False  # before we are called caller must check for existence
        )
        signup_code.save()

        invitation = cls.objects.create(
            from_user=from_user,
            message=message,
            status=Invitation.STATUS_SENT,
            signup_code=signup_code
        )

        def send_invite(*args, **kwargs):
            signup_code.send(*args, **kwargs)
            invite_sent.send(sender=cls, invitation=invitation)

        if send:
            send_invite()
        else:
            invitation.send_invite = send_invite
        return invitation
