from __future__ import unicode_literals

# Import settings from django.conf before
# importing appconf.AppConf
# https://pypi.python.org/pypi/django-appconf
from django.conf import settings

from appconf import AppConf


class InvitationsAppConf(AppConf):

    class Meta:
        prefix = "invitations"