import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class RegistrationTestCase(TestCase):
    ACCOUNT_INFO = {
        'email': 'bill@builtbykrit.com',
        'first_name': 'Bill',
        'last_name': 'Brower',
        'password': 'password125'
    }

    def register(self, account_info):
        client = Client()
        data = {
            'data': {
                'attributes': account_info,
                'type': 'users'
            }
        }
        header = {'Accept':'application/vnd.api+json'}
        return client.post('/registration/',
                           content_type='application/vnd.api+json',
                           data = json.dumps(data),
                           **header)

    def test_registration(self):
        response = self.register(self.ACCOUNT_INFO)
        assert response.status_code == 201

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        assert 'type' in data

        attributes = data['attributes']
        assert 'date_joined' in attributes
        assert 'email' in attributes
        assert 'first_name' in attributes
        assert 'last_name' in attributes
        assert attributes['email'] == self.ACCOUNT_INFO['email']
        assert attributes['first_name'] == self.ACCOUNT_INFO['first_name']
        assert attributes['last_name'] == self.ACCOUNT_INFO['last_name']

    def test_registration_with_common_password(self):
        account_info = self.ACCOUNT_INFO.copy()
        account_info['password'] = 'password'
        response = self.register(account_info)
        assert response.status_code == 400

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'errors' in json_data
        assert 'detail' in json_data['errors'][0]
        assert json_data['errors'][0]['detail'] == \
               'This password is too common.'

    def test_registration_with_email_that_is_in_use(self):
        User.objects.create_user(
            email=self.ACCOUNT_INFO['email'],
            first_name=self.ACCOUNT_INFO['first_name'],
            last_name=self.ACCOUNT_INFO['last_name'],
            password=self.ACCOUNT_INFO['password'],
            username=self.ACCOUNT_INFO['email']
        )

        response = self.register(self.ACCOUNT_INFO)
        assert response.status_code == 400

        json_data = json.loads(response.content.decode('utf-8'))
        assert 'errors' in json_data
        assert 'detail' in json_data['errors'][0]
        assert json_data['errors'][0]['detail'] == \
               'Another user is already registered using that email.'
