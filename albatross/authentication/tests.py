import json

from datetime import datetime
from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase, APIClient
from teams.models import Team


def assert_user_response_is_correct(response):
    assert response.status_code == 200
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
        assert 'type' in item
        if item['type'] == 'memberships':
            attributes = item['attributes']
            assert 'created_at' in attributes
            assert 'role' in attributes
            assert 'state' in attributes

            assert 'relationships' in item
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
        if item['type'] == 'profiles':
            attributes = item['attributes']
            assert 'harvest_access_token' in attributes
            assert 'harvest_refresh_token' in attributes
            assert 'harvest_tokens_last_refreshed_at' in attributes
            assert 'toggl_api_key' in attributes
            assert not attributes['harvest_access_token']
            assert not attributes['harvest_refresh_token']
            assert not attributes['harvest_tokens_last_refreshed_at']
            assert not attributes['toggl_api_key']


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
        header = {'Accept': 'application/json'}
        return client.post(path=reverse('login'),
                           content_type='application/json',
                           data=json.dumps(account_credentials),
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
        assert_user_response_is_correct(response)

    def test_get_user_while_unauthenticated(self):
        client = APIClient()
        response = client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 401)


class PasswordChangeTestCase(APITestCase):
    def test_change_password(self):
        # Create user
        email = 'kehoffman3@gmail.com'
        new_password = 'password126'
        old_password = 'password125'
        user = User.objects.create_user(
            email=email,
            first_name='Test',
            last_name='Account',
            password=old_password,
            username=email
        )
        self.client.force_authenticate(user=user)

        # Change password
        data = {
            'new_password1': new_password,
            'new_password2': new_password,
            'old_password': old_password
        }
        header = {'Accept': 'application/json'}
        response = self.client.post(path=reverse('change-password'),
                                    content_type='application/json',
                                    data=json.dumps(data),
                                    **header)
        self.assertEqual(response.status_code, 200)

        # Login with new password
        client = Client()
        data = {
            'email': email,
            'password': new_password
        }
        response = client.post(path=reverse('login'),
                               content_type='application/json',
                               data=json.dumps(data),
                               **header)
        self.assertEqual(response.status_code, 200)


class PasswordResetTestCase(TestCase):
    def test_reset_password(self):
        # Create user
        email = 'kehoffman3@gmail.com'
        User.objects.create_user(
            email=email,
            first_name='Test',
            last_name='Account',
            password='password126',
            username=email
        )

        # Request forgot password link
        data = {
            'email': email
        }
        header = {'Accept': 'application/json'}
        response = self.client.post(path=reverse('reset-password'),
                                    content_type='application/json',
                                    data=json.dumps(data),
                                    **header)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'detail' in json_data
        assert json_data['detail'] == 'Password reset e-mail has been sent.'


class PasswordResetConfirmationTestCase(TestCase):
    def test_reset_password(self):
        # Create user
        email = 'kehoffman3@gmail.com'
        new_password = 'password126'
        user = User.objects.create_user(
            email=email,
            first_name='Test',
            last_name='Account',
            password='password126',
            username=email
        )
        password_token_generator = PasswordResetTokenGenerator()
        token = password_token_generator.make_token(user)

        # Reset password
        data = {
            'new_password1': new_password,
            'new_password2': new_password,
            'token': token,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode('utf-8')
        }
        header = {'Accept': 'application/json'}
        response = self.client.post(path=reverse('reset-password-confirmation'),
                                    content_type='application/json',
                                    data=json.dumps(data),
                                    **header)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'detail' in json_data
        assert json_data['detail'] == 'Password has been reset with the new password.'

        # Login with new password
        data = {
            'email': email,
            'password': new_password
        }
        response = self.client.post(path=reverse('login'),
                                    content_type='application/json',
                                    data=json.dumps(data),
                                    **header)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'key' in json_data
        assert json_data['key'] is not None
        assert len(json_data['key']) == 40


class UpdateUserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        Team.objects.create(
            creator=self.user,
            name='The A Team'
        )
        self.client.force_authenticate(user=self.user)

    def test_update_user(self):
        # Get user (so we have id)
        response = self.client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content.decode('utf-8'))

        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        user_id = json_data['data']['id']

        # Update user
        new_first_name = 'Bill'
        data = {
            'data': {
                'attributes': {
                    'first_name': new_first_name
                },
                'id': user_id,
                'type': 'users'
            }
        }
        header = {'Accept': 'application/vnd.api+json'}
        response = self.client.patch(path=reverse('users'),
                                     content_type='application/vnd.api+json',
                                     data=json.dumps(data),
                                     **header)
        assert_user_response_is_correct(response)
        json_data = json.loads(response.content.decode('utf-8'))
        assert json_data['data']['attributes']['first_name'] == new_first_name


class UpdateUserProfileTestCase(APITestCase):
    def get_user_profile(self):
        response = self.client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))

        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data

        return json_data

    def setUp(self):
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_update_harvest_tokens_in_user_profile(self):
        # Get user (so we have id)
        response = self.client.get(path=reverse('users'))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content.decode('utf-8'))

        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        user_id = json_data['data']['id']

        # Update user profile
        harvest_access_token = 'adkljkajaf01'
        harvest_refresh_token = 'bdkljkajaf01'
        data = {
            'data': {
                'attributes': {
                    'harvest_access_token': harvest_access_token,
                    'harvest_refresh_token': harvest_refresh_token
                },
                'id': user_id,
                'type': 'profiles'
            }
        }
        header = {'Accept': 'application/vnd.api+json'}
        response = self.client.patch(path=reverse('users-profile',
                                                  args=(user_id,)),
                                     content_type='application/vnd.api+json',
                                     data=json.dumps(data),
                                     **header)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        assert 'harvest_access_token' in data['attributes']
        assert 'harvest_refresh_token' in data['attributes']
        assert 'harvest_tokens_last_refreshed_at' in data['attributes']
        assert data['attributes']['harvest_access_token'] == harvest_access_token
        assert data['attributes']['harvest_refresh_token'] == harvest_refresh_token
        assert datetime.strptime(data['attributes']['harvest_tokens_last_refreshed_at'],
                                 '%Y-%m-%d %H:%M:%S.%f')
        assert parser.parse(data['attributes']['harvest_tokens_last_refreshed_at'])

    def test_update_toggl_api_key_in_user_profile(self):
        # Get user (so we have id)
        user = self.get_user_profile()
        user_id = user['data']['id']

        # Update user profile
        toggl_api_key = 'adkljkajaf01'
        data = {
            'data': {
                'attributes': {
                    'toggl_api_key': toggl_api_key
                },
                'id': user_id,
                'type': 'profiles'
            }
        }
        header = {'Accept': 'application/vnd.api+json'}
        response = self.client.patch(path=reverse('users-profile',
                                                  args=(user_id,)),
                                     content_type='application/vnd.api+json',
                                     data=json.dumps(data),
                                     **header)
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        assert 'toggl_api_key' in data['attributes']
        assert data['attributes']['toggl_api_key'] == toggl_api_key
