from albatross.invitations.signals import invite_accepted

from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Team, Membership


@receiver(post_save, sender=Team)
def handle_team_save(sender, **kwargs):
    created_at = kwargs.pop("created_at")
    team = kwargs.pop("instance")
    if created_at:
        team.memberships.get_or_create(
            user=team.creator,
            defaults={
                "role": Membership.ROLE_OWNER,
                "state": Membership.STATE_JOINED
            }
        )


@receiver(invite_accepted)
def handle_invite_used(sender, invitation, **kwargs):
    for membership in invitation.memberships.all():
        membership.accept()