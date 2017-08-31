import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from teams.models import Team


class LoginTestCase(TestCase):
    ACCOUNT_CREDENTIALS = {
        'email': 'bill@builtbykrit.com',
        'password': 'password125'
    }

    def create_user(self, account_credentials):
        User.objects.create_user(
            email=account_credentials['email'],
            first_name='Test',
            last_name='Account',
            password=account_credentials['password'],
            username=account_credentials['email']
        )

    def login(self, account_credentials):
        client = Client()
        header = {'Accept':'application/json'}
        url = '/{}login/'.format(
            settings.ROOT_URLPREFIX if settings.ROOT_URLPREFIX else '')
        return client.post(url,
                           content_type='application/json',
                           data = json.dumps(account_credentials),
                           **header)

    def test_login(self):
        self.create_user(self.ACCOUNT_CREDENTIALS)

        response = self.login(self.ACCOUNT_CREDENTIALS)
        assert response.status_code == 200

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'key' in json_data
        assert json_data['key'] is not None
        assert len(json_data['key']) == 40

    def test_login_with_incorrect_password(self):
        self.create_user(self.ACCOUNT_CREDENTIALS)

        account_credentials = self.ACCOUNT_CREDENTIALS.copy()
        account_credentials['password'] = 'password'
        response = self.login(account_credentials)
        assert response.status_code == 400

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'non_field_errors' in json_data
        assert json_data['non_field_errors'] == \
               ['Unable to log in with provided credentials.']


class LogoutTestCase(APITestCase):
    def test_logout(self):
        user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(path=reverse('logout'))
        self.assertEqual(response.status_code, 200)


class GetUserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user(self):
        Team.objects.create(
            creator=self.user,
            name='The A Team'
        )

        response = self.client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content.decode('utf-8'))

        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data

        assert 'relationships' in data
        assert 'type' in data
        assert data['type'] == 'users'

        attributes = data['attributes']
        assert 'email' in attributes
        assert 'first_name' in attributes
        assert 'last_name' in attributes

        relationships = data['relationships']
        assert 'memberships' in relationships
        assert 'data' in relationships['memberships']
        assert type(relationships['memberships']['data']) == list
        assert len(relationships['memberships']['data']) == 1
        assert 'id' in relationships['memberships']['data'][0]
        assert 'type' in relationships['memberships']['data'][0]
        assert relationships['memberships']['data'][0]['type'] == 'memberships'

        assert 'included' in json_data
        included = json_data['included']
        for item in included:
            assert 'attributes' in item
            assert 'id' in item
            assert 'relationships' in item
            assert 'type' in item
            if item['type'] == 'memberships':
                attributes = item['attributes']
                assert 'created_at' in attributes
                assert 'role' in attributes
                assert 'state' in attributes

                relationships = item['relationships']
                assert 'team' in relationships
                assert 'data' in relationships['team']
                assert 'id' in relationships['team']['data']
                assert 'type' in relationships['team']['data']
                assert relationships['team']['data']['type'] == 'teams'
                assert 'user' in relationships
                assert 'id' in relationships['user']['data']
                assert 'type' in relationships['user']['data']
                assert relationships['user']['data']['type'] == 'users'

    def test_get_user_while_unauthenticated(self):
        client = APIClient()
        response = client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 401)