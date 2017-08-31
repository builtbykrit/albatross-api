import importlib

from django.apps import AppConfig as BaseAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(BaseAppConfig):

    name = "invitations"
    label = "invitations"
    verbose_name = _("Invitations")

    def ready(self):
        importlib.import_module("invitations.receivers")