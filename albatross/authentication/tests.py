import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase


class RegistrationTestCase(TestCase):
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
