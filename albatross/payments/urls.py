from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^change-card-token/$', views.ChangeCardTokenView.as_view(), name='stripe-change-card-token'),
    url(r'^details/$', views.CurrentCustomerDetailView.as_view(), name='payments-details'),
    url(r'^subscription/$', views.SubscriptionView.as_view(), name='payments-subscription'),
    url(r'^subscription/cancel/$', views.CancelView.as_view(), name='payments-subscription-cancel'),
    url(r'^webhook/$', views.WebhookView.as_view(), name='stripe-webhook'),
]
