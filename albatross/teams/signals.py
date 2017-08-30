import django.dispatch


invited_user = django.dispatch.Signal(providing_args=["membership", "by"])