import django.dispatch


update_project_line_item_times = django.dispatch.Signal(providing_args=["api_key", "project"])