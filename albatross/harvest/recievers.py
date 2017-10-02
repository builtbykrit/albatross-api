from django.dispatch import receiver
from projects.models import Project

from .hooks import hookset


@receiver('update_project_line_item_times', Sender=Project)
def handle_update_project_line_item_times(sender, **kwargs):
    api_key = kwargs.get("api_key")
    project_to_update = kwargs.get("project")
    hookset.update_project_line_item_times(api_key, project_to_update)