import hashlib
import random

from django.core.mail import EmailMultiAlternatives
from python_http_client.exceptions import BadRequestsError

from .conf import settings


MESSAGE_STRINGS = {
    "duplicate_email": "Another user is already registered using that email.",
    "invalid_signup_code": "That signup code is invalid.",
}


class RegistrationDefaultHookSet(object):

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

    def get_message_strings(self):
        return MESSAGE_STRINGS

    @staticmethod
    def send_invitation_email(to, ctx):
        signup_code = ctx["signup_code"]
        if signup_code.inviter:
            subject = "{} has invited to join an Albatross team".format(
              signup_code.inviter.get_full_name())
        else:
            subject = "You've been invited to join an Albatross team"
        mail = EmailMultiAlternatives(
            subject=subject,
            body="test",
            from_email=settings.SUPPORT_EMAIL_ADDRESS,
            reply_to=[settings.REPLY_TO_EMAIL_ADDRESS],
            to=[to]
        )
        #TODO: Update template_id
        mail.template = '3834a71f-bb2f-443a-869a-1f410fe645fa'
        mail.substitution_data = {'link': ctx["signup_url"]}

        try:
            mail.send()
        except BadRequestsError as e:
            print(e.reason)
            raise e


class HookProxy(object):

    def __getattr__(self, attr):
        return getattr(settings.REGISTRATION_HOOKSET, attr)


hookset = HookProxy()
