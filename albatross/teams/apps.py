import importlib

from django.apps import AppConfig


class TeamsConfig(AppConfig):
    name = 'teams'
    label = "teams"
    verbose_name = "Teams"

    def ready(self):
        importlib.import_module("teams.receivers")