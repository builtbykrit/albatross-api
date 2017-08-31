from django.conf.urls import url
from .views import TeamCreateView, TeamInviteView, TeamRetrieveView

urlpatterns = [
    url(r'^$', TeamCreateView.as_view(), name="teams-create"),
    url(r"^(?P<pk>[0-9]+)/$", TeamRetrieveView.as_view(), name="teams-detail"),
    url(r"^(?P<pk>[0-9]+)/invite-user/$",
        TeamInviteView.as_view(),
        name="teams-invite-user"),
]
