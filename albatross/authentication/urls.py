from django.conf.urls import url
from .views import LoginView, UserView

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^users/$', UserView.as_view(), name='users')
]