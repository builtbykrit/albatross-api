import hashlib
import random

from django.core.mail import EmailMultiAlternatives

from .conf import settings


MESSAGE_STRINGS = {
    "duplicate_email": "Another user is already registered using that email.",
    "invalid_signup_code": "That is not a valid signup code",
}


class AccountDefaultHookSet(object):

    @staticmethod
    def generate_random_token(extra=None, hash_func=hashlib.sha256):
        if extra is None:
            extra = []
        bits = extra + [str(random.SystemRandom().getrandbits(512))]
        return hash_func("".join(bits).encode("utf-8")).hexdigest()

    def generate_signup_code_token(self, email=None):
        extra = []
        if email:
            extra.append(email)
        return self.generate_random_token(extra)

    @staticmethod
    def send_invitation_email(to, ctx):
        # Using https://github.com/elbuo8/sendgrid-django
        mail = EmailMultiAlternatives(
          subject="{} has invited to join an Albatross team".format(
              ctx["inviter_name"]),
          body="",
          from_email="Andrew Askins <andrew@builtbykrit.com>",
          to=[to],
          headers={"Reply-To": "andrew@builtbykrit.com"}
        )
        mail.template_id = '3834a71f-bb2f-443a-869a-1f410fe645fa'
        mail.substitutions = {'%link%': ctx["signup_url"]}
        mail.send()

class HookProxy(object):

    def __getattr__(self, attr):
        return getattr(settings.ACCOUNT_HOOKSET, attr)


hookset = HookProxy()
