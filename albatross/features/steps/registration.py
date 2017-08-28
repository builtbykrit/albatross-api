import json

from behave import *
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import RequestsClient


@given('an email, first name, last name, and password')
def step_impl(context):
    context.account_info = {
        'email': 'bill@builtbykrit.com',
        'first_name': 'Bill',
        'last_name': 'Brower',
        'password': 'password125'
    }


@given('a user that has already registered with the given email')
def step_impl(context):
    User.objects.create_user(
        email=context.account_info['email'],
        first_name=context.account_info['first_name'],
        last_name=context.account_info['last_name'],
        password=context.account_info['password'],
        username=context.account_info['email']
    )


@when('we try to register')
def step_impl(context):
    url = context.get_url('/{}registration/'.format(
            settings.ROOT_URLPREFIX if settings.ROOT_URLPREFIX else ''))
    client = RequestsClient()
    client.headers.update({
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json'
    })
    context.response = client.post(url, json={
        'data': {
            'type': 'users',
            'attributes': context.account_info
        }
    })

@then('we should be told that the email is taken')
def step_impl(context):
    context.test.assertEqual(context.response.status_code, 400)
    json_data = json.loads(context.response.content.decode('utf-8'))
    assert 'errors' in json_data
    assert 'detail' in json_data['errors'][0]
    assert json_data['errors'][0]['detail'] == \
           'Another user is already registered using that email.'


@then('we should get a user object back')
def step_impl(context):
    context.test.assertEqual(context.response.status_code, 201)
    json_data = json.loads(context.response.content.decode('utf-8'))
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
    assert attributes['email'] == context.account_info['email']
    assert attributes['first_name'] == context.account_info['first_name']
    assert attributes['last_name'] == context.account_info['last_name']
