from datetime import datetime, timedelta
from django.conf import settings
from .utils import Harvest


def make_item_key(item):
    return "{}:{}".format(item.category.name.lower(),
                          item.description.lower())


class HarvestDefaultHookset(object):

    def update_project_line_item_times(self, api_credentials, project_to_update):
        if not project_to_update.categories.all().exists():
            return

        harvest = Harvest(access_token=api_credentials['access_token'],
                          account_id=api_credentials.get('account_id', None),
                          client_id=settings.HARVEST_CLIENT_ID,
                          client_secret=settings.HARVEST_CLIENT_SECRET,
                          refresh_token=api_credentials.get('refresh_token', None),
                          tokens_last_refreshed_at=api_credentials.get('tokens_last_refreshed_at', None))

        # Right now we are assuming that every project has a unique name
        # Note: Toggl requires a workspace id to get a detailed report
        # so we need to grab the one associated with the project
        harvest_project = None
        for project in harvest.projects():
            if project.name == project_to_update.name:
                harvest_project = project
                break
        if harvest_project is None:
            return

        # Get tasks that correspond to our categories
        all_tasks = harvest_project.task_assignments
        project_to_update_categories = project_to_update.categories.all()
        category_names = {category.name.lower() for category
                          in project_to_update_categories}
        ids_for_tasks_that_match_categories = []
        for task_data in all_tasks:
            task = task_data.task
            if task.name.lower() in category_names:
                ids_for_tasks_that_match_categories.append(task.id)

        # Grab all the time entires over the past year
        # for the project we want to update
        time_entries = project.entries()

        # Add up the durations for all of the line items
        # whose descriptions match the descriptions of our
        # project's line items.
        project_to_update_line_items = []
        for category in project_to_update_categories:
            line_items = category.items.all()
            if line_items.exists():
                project_to_update_line_items += list(line_items)
        if not project_to_update_line_items:
            return

        line_items = {make_item_key(item) : item for item
                      in project_to_update_line_items}
        line_item_totals = {make_item_key(item): 0
                            for item in project_to_update_line_items}

        for time_entry in time_entries:
            time_entry_task_name = time_entry.task.name.lower()
            item_key = "{}:{}".format(time_entry_task_name,
                                      time_entry.notes.lower())
            if item_key in line_item_totals:
                total = line_item_totals[item_key]
                total+= time_entry.hours
                line_item_totals[item_key] = total

        for item_key, total in line_item_totals.items():
            line_item = line_items[item_key]
            line_item.actual = total
            line_item.save()


class HookProxy(object):

    def __getattr__(self, attr):
        return getattr(HarvestDefaultHookset, attr)


hookset = HookProxy()