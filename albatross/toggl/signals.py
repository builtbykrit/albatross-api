import django.dispatch


pull_project_line_item_times_from_toggl = django.dispatch.Signal(providing_args=["api_key", "project"])