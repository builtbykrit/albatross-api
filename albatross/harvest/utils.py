import json

from harvest_api_client import Harvest as HarvestSuper
from harvest_api_client.harvest import instance_classes
from harvest_api_client.tokens_manager import \
    TokensManager as TokensManagerSuper


class TokensManager(TokensManagerSuper):
    def __init__(self, access_token, client_id,
                 client_secret, last_access_token_refresh_time,
                 last_refresh_token_refresh_time, refresh_token):
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.last_access_token_refresh_time = last_access_token_refresh_time
        self.last_refresh_token_refresh_time = last_refresh_token_refresh_time
        self.refresh_token = refresh_token

    def load_tokens(self):
        return
        pass

    def refresh_access_token_by_demand(self):
        if not (self.is_access_token_fresh()):
            return self.refresh_access_token()

    def refresh_access_token(self):
        json_data = self._refresh_access_token_impl()
        old_json_file_data = self.load_tokens()
        self.write_tokens({
            'access_token': {
                self.value_key: json_data['access_token'],
                self.last_refresh_time_key: datetime.datetime.now().isoformat()
            },
            'refresh_token': {
                self.value_key: json_data['refresh_token'],
                self.last_refresh_time_key: old_json_file_data['refresh_token'][self.last_refresh_time_key]
            }
        })

        print('\nThe access token has been refreshed.\n')

    def write_tokens(self, json_data):
        # We won't actually use this method
        pass


class Harvest(HarvestSuper):
    def __init__(self, access_token, client_id, client_secret, refresh_token):
        self.headers = {}
        self.tokens_man = TokensManager(access_token, client_id,
                                        client_secret, refresh_token)
        self.access_token = self.tokens_man.load_tokens()['access_token']['value']
        self.uri = 'https://api.harvestapp.com'
        self.headers['Accept'] = 'application/xml'
        self.headers['Content-Type'] = 'application/xml'
        self.headers['User-Agent'] = 'py-harvest.py'
        for klass in instance_classes:
            self._create_getters(klass)