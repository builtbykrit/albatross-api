import json

from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from teams.models import Team


class TeamViewsTestCase(APITestCase):
    TEAM_INFO = {
        'name': 'The A Team'
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email='kehoffman3@gmail.com',
            first_name='Test',
            last_name='Account',
            password='password125',
            username='kehoffman3@gmail.com'
        )
        self.client.force_authenticate(user=self.user)

    def assert_team_response_is_correct(self, response):
        json_data = json.loads(response.content.decode('utf-8'))

        assert 'data' in json_data
        data = json_data['data']
        assert 'attributes' in data
        assert 'id' in data
        assert 'relationships' in data
        assert 'type' in data
        assert data['type'] == 'teams'

        attributes = data['attributes']
        assert 'created_at' in attributes
        assert 'name' in attributes
        assert 'on_trial' in attributes
        assert 'trial_expires_at' in attributes
        assert attributes['name'] == self.TEAM_INFO['name']
        assert attributes['on_trial'] == False
        assert (datetime.strptime(attributes['trial_expires_at'],
                                      "%Y-%m-%dT%H:%M:%S.%fZ")
                    - datetime.now()
                    > timedelta(days=13))

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
        assert type(included) == list
        for item in included:
            assert 'attributes' in item
            assert 'id' in item
            assert 'relationships' in item
            assert 'type' in item

    def create_team(self, client):
        data = {
            'data': {
                'attributes': self.TEAM_INFO,
                'type': 'teams'
            }
        }
        return client.post(data=json.dumps(data),
                           path=reverse('teams-create'),
                           content_type='application/vnd.api+json')

    def test_create_team(self):
        response = self.create_team(client=self.client)
        self.assertEqual(response.status_code, 201)
        self.assert_team_response_is_correct(response)

    def test_create_team_while_unauthenticated(self):
        client = APIClient()
        response = self.create_team(client=client)
        self.assertEqual(response.status_code, 401)

    def test_get_team(self):
        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        response = self.client.get(reverse('teams-detail', args=(team.id,)))
        self.assertEqual(response.status_code, 200)
        self.assert_team_response_is_correct(response)

    def test_get_team_while_unauthenticated(self):
        client = APIClient()

        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        response = client.get(reverse('teams-detail', args=(team.id,)))
        self.assertEqual(response.status_code, 401)

    def test_invite_to_team(self):
        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        data = {'email':'bill@builtbykrit.com'}
        response = self.client.post(data=json.dumps(data),
                                    path=reverse('teams-invite-user', args=(team.id,)),
                                    content_type='application/json')
        print(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 204)

    def test_invite_to_team_while_unauthenticated(self):
        client = APIClient()

        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        data = {'email':'bill@builtbykrit.com'}
        response = client.post(data=json.dumps(data),
                               path=reverse('teams-invite-user', args=(team.id,)),
                               content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_invite_to_team_with_pending_invitation(self):

        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        data = {'email': 'bill@builtbykrit.com'}
        self.client.post(data=json.dumps(data),
                         path=reverse('teams-invite-user', args=(team.id,)),
                         content_type='application/json')

        response = self.client.post(data=json.dumps(data),
                               path=reverse('teams-invite-user', args=(team.id,)),
                               content_type='application/json')

        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.content.decode('utf-8'))
        errors = json_response['errors']
        self.assertEqual(errors[0]['detail'], "The email address you entered has already been invited to join a team.")

    def test_invite_to_team_when_a_user(self):

        team = Team.objects.create(
            creator=self.user,
            name=self.TEAM_INFO['name']
        )

        data = {'email': 'kehoffman3@gmail.com'}

        response = self.client.post(data=json.dumps(data),
                               path=reverse('teams-invite-user', args=(team.id,)),
                               content_type='application/json')

        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.content.decode('utf-8'))
        errors = json_response['errors']
        self.assertEqual(errors[0]['detail'], "This user is already apart of a team.")