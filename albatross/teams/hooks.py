from .conf import settings


MESSAGE_STRINGS = {
    "invite-already-sent": "Invite already sent.",
}


class TeamDefaultHookset(object):

    def get_message_strings(self):
        return MESSAGE_STRINGS

    def user_is_staff(self, user):
        # @@@ consider staff users managers of any Team
        return getattr(user, "is_staff", False)


class HookProxy(object):

    def __getattr__(self, attr):
        return getattr(settings.TEAMS_HOOKSET, attr)


hookset = HookProxy()