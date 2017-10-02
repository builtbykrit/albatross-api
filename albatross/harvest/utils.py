import json

from django.utils import timezone
from harvest_api_client import Harvest as HarvestSuper
from harvest_api_client.harvest import instance_classes
from harvest_api_client.tokens_manager import \
    TokensManager as TokensManagerSuper


class TokensManager(TokensManagerSuper):
    def __init__(self, access_token, client_id,
                 client_secret, refresh_token,
                 tokens_last_refreshed_at):
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.last_refresh_time = tokens_last_refreshed_at
        self.refresh_token = refresh_token

    def load_tokens(self):
        return {
            'access_token': {
                self.value_key: self.access_token,
                self.last_refresh_time_key: self.last_refresh_time
            },
            'refresh_token': {
                self.value_key: self.refresh_token,
                self.last_refresh_time_key: self.last_refresh_time
            }
        }

    def refresh_access_token_by_demand(self):
        if not (self.is_access_token_fresh()):
            return self.refresh_access_token()

    def refresh_access_token(self):
        json_data = self._refresh_access_token_impl()
        self.last_refresh_time = timezone.now()
        return {
            'access_token': {
                self.value_key: json_data['access_token'],
                self.last_refresh_time_key: self.last_refresh_time
            },
            'refresh_token': {
                self.value_key: json_data['refresh_token'],
                self.last_refresh_time_key: self.last_refresh_time
            }
        }

    def write_tokens(self, json_data):
        raise Exception('harvest.utils.TokensManager.write_tokens '
                        'should not be used')


class Harvest(HarvestSuper):
    def __init__(self, access_token, client_id, client_secret,
                 refresh_token, tokens_last_refreshed_at):
        self.headers = {}
        self.tokens_man = TokensManager(access_token,
                                        client_id,
                                        client_secret,
                                        refresh_token,
                                        tokens_last_refreshed_at)
        self.access_token = access_token
        self.uri = 'https://api.harvestapp.com'
        self.headers['Accept'] = 'application/xml'
        self.headers['Content-Type'] = 'application/xml'
        self.headers['User-Agent'] = 'py-harvest.py'
        for klass in instance_classes:
            self._create_getters(klass)