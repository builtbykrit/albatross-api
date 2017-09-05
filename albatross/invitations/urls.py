from django.conf.urls import url
from .views import InvitationDetailView

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/$', InvitationDetailView.as_view(), name='invitations-detail')
]