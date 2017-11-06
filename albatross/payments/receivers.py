from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from drfstripe.signals import (
    cancelled,
    card_changed,
    subscription_made,
    webhook_processing_error,
    WEBHOOK_SIGNALS
)
from python_http_client.exceptions import BadRequestsError

from .conf import settings


def send_mail(mail):
    try:
        mail.send()
    except BadRequestsError as e:
        print(e.reason)
        raise e


@receiver(cancelled)
def handle_cancelled(sender, stripe_response, **kwargs):
    # I don't think we need to do anything here
    pass

@receiver(card_changed)
def handle_card_changed(sender, stripe_response, **kwargs):
    # I don't think we need to do anything here
    pass

@receiver(WEBHOOK_SIGNALS['charge.failed'])
def handle_charge_failed(sender, event, **kwargs):
    """Send a "Dunning" email

    Keyword Args:
        event -- a drfstripe.models.event object"""
    user = event.customer.user
    mail = EmailMultiAlternatives(
        subject="Uh oh, your card failed - update your billing "
                "info to keep using Albatross",
        body="test",
        from_email=settings.SUPPORT_EMAIL_ADDRESS,
        reply_to=[settings.REPLY_TO_EMAIL_ADDRESS],
        to=[user.email],
        bcc=["andrew@builtbykrit.com",
             "austin@builtbykrit.com",
             "bill@builtbykrit.com"]
    )
    mail.substitution_data = {'name': user.first_name}
    mail.template = 'dunning'
    send_mail(mail)

@receiver(WEBHOOK_SIGNALS['customer.subscription.deleted'])
def handle_subscription_deleted(sender, event, **kwargs):
    """Send a "Subscription expired" email

    Keyword Args:
        event -- a drfstripe.models.event object"""
    user = event.customer.user
    mail = EmailMultiAlternatives(
        subject="Your Subscription to Albatross Just Ended - Renew Now",
        body="test",
        from_email=settings.SUPPORT_EMAIL_ADDRESS,
        reply_to=[settings.REPLY_TO_EMAIL_ADDRESS],
        to=[user.email]
    )
    mail.substitution_data = {'name': user.first_name}
    mail.template = 'subscription-expired'
    send_mail(mail)

@receiver(subscription_made)
def handle_subscription_made(sender, plan, stripe_response, **kwargs):
    """Send a "Thanks for upgrading" email

    Keyword Args:
        plan -- an entry from the PAYMENTS_PLANS dictionary in the settings
        stripe_response -- a json response from Stripe"""
    mail = EmailMultiAlternatives(
        subject="You're Officially Subscribed to Albatross!",
        body="test",
        from_email=settings.SUPPORT_EMAIL_ADDRESS,
        reply_to=[settings.REPLY_TO_EMAIL_ADDRESS],
        to=[sender.user.email]
    )
    mail.template = 'upgrade'
    send_mail(mail)

@receiver(webhook_processing_error)
def handle_webhook_processing_error(sender, data, **kwargs):
    """Email Bill about it """
    mail = EmailMultiAlternatives(
        subject="Albatross Webhook Processing Error",
        body="test",
        from_email=settings.SUPPORT_EMAIL_ADDRESS,
        reply_to=[settings.REPLY_TO_EMAIL_ADDRESS],
        to=["bill@builtbykrit.com"]
    )
    send_mail(mail)