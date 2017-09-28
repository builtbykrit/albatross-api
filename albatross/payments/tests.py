import json

from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from teams.models import Membership, Team


def change_card_token(client, new_token):
    data = {
        'token': new_token
    }
    header = {'Accept': 'application/json'}

    return client.post(reverse('stripe-change-card-token'),
                       content_type='application/json',
                       data=json.dumps(data),
                       **header)


class ChangeCardTokenTestCase(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=user)

    def test_change_card_token(self):
        new_token = 'tok_visa'
        response = change_card_token(self.client, new_token)
        assert response.status_code == 201

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'token' in json_data
        assert json_data['token'] == new_token


class PaymentDetailsTestCase(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=user)
        change_card_token(self.client, 'tok_visa')

    def test_get_payment_details(self):
        response = self.client.get(reverse('payments-details'))
        assert response.status_code == 200

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'can_charge' in json_data
        assert 'card_fingerprint' in json_data
        assert 'card_last_4' in json_data
        assert 'card_kind' in json_data
        assert 'created_at' in json_data
        assert 'date_purged' in json_data
        assert 'has_active_subscription' in json_data
        assert 'id' in json_data
        assert 'stripe_id' in json_data
        assert 'user' in json_data
        #
        assert json_data['can_charge'] == True
        assert json_data['card_last_4'] == '4242'
        assert json_data['card_kind'] == 'Visa'
        assert not json_data['date_purged']
        assert not json_data['has_active_subscription']
        assert 'cus_' in json_data['stripe_id']

class SubscriptionTestCase(APITestCase):
    def assert_valid_subscription_response(self, response, plan_id):
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'amount' in json_data
        assert 'cancel_at_period_end' in json_data
        assert 'canceled_at' in json_data
        assert 'created_at' in json_data
        assert 'currency' in json_data
        assert 'current_period_end' in json_data
        assert 'current_period_start' in json_data
        assert 'customer' in json_data
        assert 'ended_at' in json_data
        assert 'id' in json_data
        assert 'plan' in json_data
        assert 'quantity' in json_data
        assert 'start' in json_data
        assert 'status' in json_data
        assert 'trial_end' in json_data
        assert 'trial_start' in json_data
        #
        assert not json_data['cancel_at_period_end']
        assert not json_data['canceled_at']
        assert datetime.strptime(json_data['current_period_end'], '%Y-%m-%dT%H:%M:%SZ')
        assert datetime.strptime(json_data['current_period_start'], '%Y-%m-%dT%H:%M:%SZ')
        assert not json_data['ended_at']
        assert type(json_data['id']) == int
        assert json_data['plan'] == plan_id
        assert json_data['quantity'] == 1
        assert datetime.strptime(json_data['start'], '%Y-%m-%dT%H:%M:%SZ')
        assert json_data['status'] == 'active'
        assert not json_data['trial_end']
        assert not json_data['trial_start']

    def change_subscription(self, stripe_plan):
        data = {
            'stripe_plan': stripe_plan
        }
        header = {'Accept': 'application/json'}

        return self.client.post(reverse('payments-subscription'),
                                content_type='application/json',
                                data=json.dumps(data),
                                **header)

    def setUp(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.team = Team.objects.create(
            creator=user,
            name='The A Team'
        )
        self.client.force_authenticate(user=user)
        change_card_token(self.client, 'tok_visa')

    def test_get_subscription_while_unsubscribed(self):
        response = self.client.get(reverse('payments-subscription'))
        assert response.status_code == 200

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'amount' in json_data
        assert 'cancel_at_period_end' in json_data
        assert 'canceled_at' in json_data
        assert 'created_at' in json_data
        assert 'currency' in json_data
        assert 'current_period_end' in json_data
        assert 'current_period_start' in json_data
        assert 'customer' in json_data
        assert 'ended_at' in json_data
        assert 'plan' in json_data
        assert 'quantity' in json_data
        assert 'start' in json_data
        assert 'status' in json_data
        assert 'trial_end' in json_data
        assert 'trial_start' in json_data

        assert not json_data['amount']
        assert not json_data['cancel_at_period_end']
        assert not json_data['canceled_at']
        assert not json_data['created_at']
        assert not json_data['currency']
        assert not json_data['current_period_end']
        assert not json_data['current_period_start']
        assert not json_data['customer']
        assert not json_data['ended_at']
        assert not json_data['plan']
        assert not json_data['quantity']
        assert not json_data['start']
        assert not json_data['status']
        assert not json_data['trial_end']
        assert not json_data['trial_start']

    def test_subscribe(self):
        plan_id = 'agency-beta-monthly'
        response = self.change_subscription(plan_id)
        assert response.status_code == 201

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'cancel_at_period_end' in json_data
        assert 'canceled_at' in json_data
        assert 'current_period_end' in json_data
        assert 'current_period_start' in json_data
        assert 'customer' in json_data
        assert 'ended_at' in json_data
        assert 'plan' in json_data
        assert 'quantity' in json_data
        assert 'start' in json_data
        assert 'status' in json_data
        assert 'trial_end' in json_data
        assert 'trial_start' in json_data

        assert not json_data['cancel_at_period_end']
        assert not json_data['canceled_at']
        assert type(json_data['current_period_end']) == int
        assert type(json_data['current_period_start']) == int
        assert 'cus_' in json_data['customer']
        assert not json_data['ended_at']
        assert type(json_data['plan']) == dict
        assert json_data['quantity'] == 1
        assert type(json_data['start']) == int
        assert json_data['status'] == 'active'
        assert not json_data['trial_end']
        assert not json_data['trial_start']

        plan = json_data['plan']
        assert 'amount' in plan
        assert 'currency' in plan
        assert 'id' in plan
        assert 'interval' in plan
        assert 'interval_count' in plan
        assert 'name' in plan
        assert 'statement_description' in plan
        assert 'statement_descriptor' in plan
        #
        assert plan['amount'] == 2500
        assert plan['currency'] == 'usd'
        assert plan['id'] == plan_id
        assert plan['interval'] == 'month'
        assert plan['interval_count'] == 1
        assert plan['name'] == 'Agency Beta Monthly'
        assert plan['statement_description'] == 'Albatross App'
        assert plan['statement_descriptor'] == 'Albatross App'

    def test_get_subscription(self):
        plan_id = 'agency-beta-monthly'
        self.change_subscription(plan_id)
        response = self.client.get(reverse('payments-subscription'))
        assert response.status_code == 200
        self.assert_valid_subscription_response(response, plan_id)

    def test_get_subscription_as_team_member(self):
        plan_id = 'agency-beta-monthly'
        self.change_subscription(plan_id)

        user = User.objects.create_user(
            email='kehoffman3s_friend@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3s_friend@gmail.com'
        )
        Membership.objects.create(
            team=self.team,
            user=user
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('payments-subscription'))
        assert response.status_code == 200
        self.assert_valid_subscription_response(response, plan_id)

    def test_cancel_subscription(self):
        data = {
            'confirm': True
        }
        header = {'Accept': 'application/json'}
        response = self.client.post(reverse('payments-subscription-cancel'),
                                    content_type='application/json',
                                    data=json.dumps(data),
                                    **header)
        assert response.status_code == 202
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'success' in json_data
        assert json_data['success'] == True

        response = self.client.get(reverse('payments-details'))
        assert response.status_code == 200
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'has_active_subscription' in json_data
        assert not json_data['has_active_subscription']

