from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.core.urlresolvers import reverse
from django.utils import timezone
from invitations.models import Invitation

from . import signals
from .conf import settings
from .hooks import hookset


class BaseMembership(models.Model):
    created_at = models.DateTimeField(default=timezone.now,
                                      editable=False,
                                      verbose_name="created at")

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

    class JSONAPIMeta:
        resource_name = "memberships"

    class Meta:
        abstract = True
        verbose_name = "Base Membership"
        verbose_name_plural = "Bases Memberships"

    @property
    def invitee(self):
        return self.user or self.invitation.to_user_email()

    def is_member(self):
        return self.role == BaseMembership.ROLE_MEMBER

    def is_owner(self):
        return self.role == BaseMembership.ROLE_OWNER

    def status(self):
        if self.user:
            return self.get_state_display()
        if self.invitation:
            return self.invitation.get_status_display()
        return "Unknown"


class BaseTeam(models.Model):
    class JSONAPIMeta:
        resource_name = "teams"

    class Meta:
        abstract = True
        verbose_name = "Base Team"
        verbose_name_plural = "Bases Teams"

    @property
    def acceptances(self):
        return self.memberships.filter(state=BaseMembership.STATE_JOINED)

    @property
    def invitees(self):
        return self.memberships.filter(state=BaseMembership.STATE_INVITED)

    @property
    def members(self):
        return self.acceptances.filter(role=BaseMembership.ROLE_MEMBER)

    @property
    def owners(self):
        return self.acceptances.filter(role=BaseMembership.ROLE_OWNER)

    def can_join(self, user):
        if self.state_for(user) == BaseMembership.STATE_INVITED:
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
                    role=BaseMembership.ROLE_MEMBER, message=None):
        if not Invitation.objects.filter(signup_code__email=to_email).exists():
            invite = Invitation.invite(from_user, to_email,
                                       message, send=False)
            membership, created = self.memberships.get_or_create(
                invitation=invite,
                defaults={"role": role, "state": BaseMembership.STATE_INVITED}
            )
            invite.send_invite()
            signals.invited_user.send(sender=self, membership=membership)
            return membership

    def role_for(self, user):
        if hookset.user_is_staff(user):
            return BaseMembership.ROLE_MANAGER

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

class Team(BaseTeam):
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


class Membership(BaseMembership):
    invitation = models.ForeignKey(Invitation,
                                   related_name="memberships",
                                   null=True,
                                   blank=True,
                                   verbose_name="invitation")

    team = models.ForeignKey(Team,
                             related_name="memberships",
                             verbose_name="team")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="memberships",
                             null=True,
                             blank=True,
                             verbose_name="user")

    def accept(self):
        self.user = self.invitation.to_user
        self.state = BaseMembership.STATE_JOINED
        self.save()

    def __str__(self):
        return "{0} in {1}".format(self.user, self.team)

    class Meta:
        unique_together = [("team", "user", "invitation")]
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
