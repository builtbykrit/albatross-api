from django.conf.urls import url
from .views import TeamListCreateView, TeamInviteView

urlpatterns = [
    url(r'^$', TeamListCreateView.as_view(), name='teams'),
    url(r"^teams/(?P<pk>[0-9]+)/invite-user/$", TeamInviteView.as_view(),
        name="teams_invite_user"),
]
