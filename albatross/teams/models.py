from albatross.invitations.models import Invitation

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.core.urlresolvers import reverse
from django.utils import timezone

from . import signals
from .conf import settings
from .hooks import hookset


class Membership(models.Model):
    created_at = models.DateTimeField(default=timezone.now,
                                      editable=False,
                                      verbose_name="created at")

    invite = models.ForeignKey(Invitation,
                               related_name="memberships",
                               null=True,
                               blank=True,
                               verbose_name=_("invite"))

    ROLE_MEMBER = "member"
    ROLE_OWNER = "owner"
    ROLE_CHOICES = [
        (ROLE_MEMBER, "member"),
        (ROLE_OWNER, "owner")
    ]
    role = models.CharField(max_length=20,
                            choices=ROLE_CHOICES,
                            default=ROLE_MEMBER,
                            verbose_name="role")

    STATE_INVITED = "invited"
    STATE_JOINED = "joined"
    STATE_CHOICES = [
        (STATE_INVITED, "invited"),
        (STATE_JOINED, "joined")
    ]
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        verbose_name="state")

    team = models.ForeignKey(Team,
                             related_name="memberships",
                             verbose_name="team")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="memberships",
                             null=True,
                             blank=True,
                             verbose_name="user")

    def __str__(self):
        return "{0} in {1}".format(self.user, self.team)

    class Meta:
        unique_together = [("team", "user", "invite")]
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    @property
    def invitee(self):
        return self.user or self.invite.to_user_email()

    def accept(self, by):
        self.state = Membership.STATE_JOINED
        self.save()

    def is_member(self):
        return self.role == Membership.ROLE_MEMBER

    def is_owner(self):
        return self.role == Membership.ROLE_OWNER

    def status(self):
        if self.user:
            return self.get_state_display()
        if self.invite:
            return self.invite.get_status_display()
        return "Unknown"


class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="name")
    created_at = models.DateTimeField(default=timezone.now,
                                      editable=False,
                                      verbose_name="created at")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name="teams_created",
                                verbose_name="creator")

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def get_absolute_url(self):
        return reverse("team_detail", args=[self.slug])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Team, self).save(*args, **kwargs)

    @property
    def acceptances(self):
        return self.memberships.filter(state=Membership.STATE_JOINED)

    @property
    def invitees(self):
        return self.memberships.filter(state=Membership.STATE_INVITED)

    @property
    def members(self):
        return self.acceptances.filter(role=Membership.ROLE_MEMBER)

    @property
    def owners(self):
        return self.acceptances.filter(role=Membership.ROLE_OWNER)

    def can_join(self, user):
        if self.state_for(user) == Membership.STATE_INVITED:
            return True
        else:
            return False

    def is_member(self, user):
        return self.members.filter(user=user).exists()

    def is_owner(self, user):
        return self.owners.filter(user=user).exists()

    def is_on_team(self, user):
        return self.acceptances.filter(user=user).exists()

    def invite_user(self, from_user, to_email,
                    role=Membership.ROLE_MEMBER, message=None):
        if not Invitation.objects.filter(signup_code__email=to_email).exists():
            invite = Invitation.invite(from_user, to_email,
                                       message, send=False)
            membership, created = self.memberships.get_or_create(
                invite=invite,
                defaults={"role": role, "state": Membership.STATE_INVITED}
            )
            invite.send_invite()
            signals.invited_user.send(sender=self, membership=membership)
            return membership

    def role_for(self, user):
        if hookset.user_is_staff(user):
            return Membership.ROLE_MANAGER

        membership = self.for_user(user)
        if membership:
            return membership.role

    def state_for(self, user):
        membership = self.for_user(user=user)
        if membership:
            return membership.state

    def team_for(self, user):
        try:
            return self.memberships.get(user=user)
        except ObjectDoesNotExist:
            pass






