import importlib, six

# Import settings from django.conf before
# importing appconf.AppConf
# https://pypi.python.org/pypi/django-appconf
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from appconf import AppConf


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = importlib.import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured("Error importing {0}: '{1}'".format(module, e))
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured("Module '{0}' does not define a '{1}'".format(module, attr))
    return attr


PAYMENTS_PLANS = getattr(settings, "PAYMENTS_PLANS", {})


def get_api_key():
        return settings.STRIPE_SECRET_KEY

def plan_from_stripe_id(stripe_id):
        for key in PAYMENTS_PLANS.keys():
            if PAYMENTS_PLANS[key].get("stripe_plan_id") == stripe_id:
                return key

settings.get_api_key = get_api_key
settings.plan_from_stripe_id = plan_from_stripe_id


class PaymentsConfig(AppConf):
    name = 'payments'
    label = 'payments'
    verbose_name = 'payments'

    DEFAULT_PLAN = getattr(
        settings,
        "PAYMENTS_DEFAULT_PLAN",
        None
    )

    INVOICE_FROM_EMAIL = getattr(
        settings,
        "PAYMENTS_INVOICE_FROM_EMAIL",
        "billing@example.com"
    )

    PAYMENTS_PLANS = PAYMENTS_PLANS

    PLAN_CHOICES = [
        (plan, PAYMENTS_PLANS[plan].get("name", plan))
        for plan in PAYMENTS_PLANS
    ]

    PLAN_QUANTITY_CALLBACK = getattr(
        settings,
        "PAYMENTS_PLAN_QUANTITY_CALLBACK",
        None
    )
    if isinstance(PLAN_QUANTITY_CALLBACK, six.string_types):
        PLAN_QUANTITY_CALLBACK = load_path_attr(PLAN_QUANTITY_CALLBACK)

    TRIAL_PERIOD_FOR_USER_CALLBACK = getattr(
        settings,
        "PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK",
        None
    )
    if isinstance(TRIAL_PERIOD_FOR_USER_CALLBACK, six.string_types):
        TRIAL_PERIOD_FOR_USER_CALLBACK = load_path_attr(
            TRIAL_PERIOD_FOR_USER_CALLBACK
        )

    SEND_EMAIL_RECEIPTS = getattr(settings, "SEND_EMAIL_RECEIPTS", True)

    STRIPE_PUBLIC_KEY = settings.STRIPE_PUBLIC_KEY
