import stripe

from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.encoding import smart_str

from rest_framework import status, generics
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from drfstripe.api.serializers import (
    CardTokenSerializer,
    CancelSerializer,
    CurrentSubscriptionSerializer,
    CurrentCustomerSerializer,
    EventSerializer,
    EventProcessingExceptionSerializer,
    SubscriptionSerializer,
    WebhookSerializer
)

from drfstripe.models import (
    Event,
    EventProcessingException
)

from .conf import settings as app_settings
from .models import CurrentSubscription, Customer


stripe.api_key = app_settings.get_api_key()


class StripeView(APIView):
    """ Generic API StripeView """
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)
    permission_classes = (IsAuthenticated, )

    def get_current_subscription(self):
        try:
            team = self.get_users_team()
            if not team:
                return None
            return team.current_subscription
        except CurrentSubscription.DoesNotExist:
            return None

    def get_customer(self):
        try:
            return self.request.user.customer
        except ObjectDoesNotExist:
            return Customer.create(self.request.user)

    def get_users_team(self):
        try:
            memberships = self.request.user.memberships
            membership = memberships.first()
            if not membership:
                return None
            return membership.team
        except ObjectDoesNotExist:
            return None


class CancelView(StripeView):
    """ Cancel customer subscription """
    serializer_class = CancelSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                customer = self.get_customer()
                customer.cancel()
                return Response({'success': True}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except stripe.StripeError as e:
            error_data = {u'error': smart_str(e) or u'Unknown error'}
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class ChangeCardTokenView(StripeView):
    """
    Add or update customer card token

    This is useful if you are planing to use strip.js to
    retrieve the card token. This isolates the full credit
    card number from your server.
    """
    serializer_class = CardTokenSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                validated_data = serializer.validated_data

                customer = self.get_customer()

                token = validated_data['token']
                customer.update_card(token)
                send_invoice = customer.card_fingerprint == ""

                if send_invoice:
                    customer.send_invoice()
                    customer.retry_unpaid_invoices()

                return Response(validated_data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except stripe.StripeError as e:
            error_data = {u'error': smart_str(e) or u'Unknown error'}
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            customer = self.get_customer()
            customer.delete_card()
            return Response({'success': True}, status=status.HTTP_202_ACCEPTED)
        except stripe.StripeError as e:
            error_data = {u'error': smart_str(e) or u'Unknown error'}
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class CurrentCustomerDetailView(StripeView, generics.RetrieveAPIView):
    """ See the current customer/user payment details """
    serializer_class = CurrentCustomerSerializer

    def get_object(self):
        return self.get_customer()


class SubscriptionView(StripeView):
    """ See, change/set the current customer/user subscription plan """
    serializer_class = SubscriptionSerializer

    def get(self, request, *args, **kwargs):
        current_subscription = self.get_current_subscription()
        serializer = CurrentSubscriptionSerializer(current_subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                # Subscribe to the plan. Note that customer.subscribe returns
                # Stripe's response, not a CurrentSubscription db model.
                #
                # So we need to call customer.current_subscription to set
                # the subscriptions team.
                validated_data = serializer.validated_data
                stripe_plan = validated_data.get('stripe_plan', None)
                customer = self.get_customer().customer
                subscription = customer.subscribe(stripe_plan) # this is Stripe's response

                team = self.get_users_team()
                current_subscription = customer.current_subscription
                current_subscription.team = team
                current_subscription.save()

                return Response(subscription, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except stripe.StripeError as e:
            from django.utils.encoding import smart_str

            error_data = {u'error': smart_str(e) or u'Unknown error'}
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class WebhookView(StripeView):
    serializer_class = WebhookSerializer

    def validate_webhook(self, webhook_data):
        webhook_id = webhook_data.get('id', None)
        webhook_type = webhook_data.get('type', None)
        webhook_livemode = webhook_data.get('livemode', None)
        is_valid = False

        if webhook_id and webhook_type and webhook_livemode:
            is_valid = True
        return is_valid, webhook_id, webhook_type, webhook_livemode

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                validated_data = serializer.validated_data
                webhook_data = validated_data.get('data', None)

                is_webhook_valid, webhook_id, webhook_type, webhook_livemode = self.validate_webhook(webhook_data)

                if is_webhook_valid:
                    if Event.objects.filter(stripe_id=webhook_id).exists():
                        obj = EventProcessingException.objects.create(
                            data=validated_data,
                            message="Duplicate event record",
                            traceback=""
                        )

                        event_processing_exception_serializer = EventProcessingExceptionSerializer(obj)
                        return Response(event_processing_exception_serializer.data, status=status.HTTP_200_OK)
                    else:
                        event = Event.objects.create(
                            stripe_id=webhook_id,
                            kind=webhook_type,
                            livemode=webhook_livemode,
                            webhook_message=validated_data
                        )
                        event.validate()
                        event.process()
                        event_serializer = EventSerializer(event)
                        return Response(event_serializer.data, status=status.HTTP_200_OK)
                else:
                    error_data = {u'error': u'Webhook must contain id, type and livemode.'}
                    return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except stripe.StripeError as e:
            error_data = {u'error': smart_str(e) or u'Unknown error'}
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)