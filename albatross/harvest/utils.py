import json, requests

from dateutil.parser import parse as parseDate
from django.utils import timezone
from harvest_api_client import Harvest as HarvestSuper
from harvest_api_client.harvest import (
    HarvestConnectionError,
    HarvestError,
    instance_classes
)
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
        if json_data is None:
            return None
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

    def _refresh_access_token_impl(self):
        tokens = self.load_tokens()
        body = 'refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token'.format(
            refresh_token=tokens['refresh_token'][self.value_key], client_id=self.client_id,
            client_secret=self.client_secret
        )
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
        resp = requests.post('https://api.harvestapp.com/v2/oauth2/token', headers=headers, data=body, verify=False)
        if resp.status_code >= 400:
            return None
        return json.loads(resp.content.decode())


class Harvest(HarvestSuper):
    def __init__(self, access_token, client_id, client_secret,
                 refresh_token=None, tokens_last_refreshed_at=None,
                 account_id=None):
        self.headers = {}
        self.tokens_man = TokensManager(access_token,
                                        client_id,
                                        client_secret,
                                        refresh_token,
                                        tokens_last_refreshed_at)
        self.access_token = access_token
        self.account_id = account_id
        self.uri = 'https://api.harvestapp.com/v2'
        self.headers['Accept'] = 'application/json'
        self.headers['Content-Type'] = 'application/json'
        self.headers['User-Agent'] = 'py-harvest.py'
        for klass in instance_classes:
            self._create_getters(klass)

    def _create_getters(self, klass):
        '''
        This method creates both the singular and plural getters for various
        Harvest object classes.
        '''
        flag_name = '_got_' + klass.element_name
        cache_name = '_' + klass.element_name
        setattr(self, cache_name, {})
        setattr(self, flag_name, False)
        cache = getattr(self, cache_name)

        def _get_item(id):
            if id in cache:
                return cache[id]
            else:
                url = '{}/{}'.format(klass.base_url, id)
                try:
                    item = next(self._get_element_values(url))
                    item = klass(self, item)
                    cache[id] = item
                    return item
                except StopIteration:
                    pass

        setattr(self, klass.element_name, _get_item)

        def _get_items():
            if getattr(self, flag_name):
                for item in cache.values():
                    yield item
            else:
                for element in self._get_element_values(klass.base_url, klass.plural_name):
                    item = klass(self, element)
                    cache[item.id] = item
                    yield item

                setattr(self, flag_name, True)

        setattr(self, klass.plural_name, _get_items)

    def _get_element_values(self, url, tagname=None, query_params={}):
        response = self._request(url, query_params)
        if tagname:
            elements = response.get(tagname, {})
            for element in elements:
                yield dict(element)
        else:
            yield response

    def _request(self, url, query_params={}):
        full_url = self.uri + url

        query_params['access_token'] = self.access_token
        if self.account_id:
            query_params['account_id'] = self.account_id

        try:
            # if refresh_token is fresh then the access token can be refreshed
            # by sending a GET request to a specific url according to the spec of OAuth2
            # but if isn't fresh then an user must re-authenticate to obtain the new access and refresh tokens
            if self.account_id:
                # If we are specifying an account id then we're using
                # a personal token which won't expire
                pass
            elif self.tokens_man.is_refresh_token_fresh():
                self.tokens_man.refresh_access_token_by_demand()
            else:
                raise HarvestError('You must re-authenticate')

            return requests.get(full_url,
                                headers=self.headers,
                                params=query_params).json()
        except (requests.ConnectionError,
                requests.Timeout,
                requests.TooManyRedirects) as e:
            raise HarvestConnectionError(e)

    def _time_entries(self, start=None, end=None, query_params={}):
        url = '/time_entries'

        if start:
            query_params['from'] = start.isoformat()
        if end:
            query_params['to'] = end.isoformat()

        for element in self._get_element_values(url,
                                                tagname='time_entries',
                                                query_params=query_params):
            yield Entry(self, element)


class HarvestItemBase(object):
    def __init__(self, harvest, data):
        self.harvest = harvest
        for key, value in data.items():
            key = key.replace('-', '_').replace(' ', '_')
            try:
                if hasattr(self, key) or hasattr(self.__class__, key):
                    key = '_{}'.format(key)
                setattr(self, key, value)
            except AttributeError:
                pass


class HarvestItemGetterable(type):
    def __init__(klass, name, bases, attrs):
        # super(HarvestItemGetterable, klass).__init__(name, bases, attrs)
        super().__init__(name, bases, attrs)
        instance_classes.append(klass)


class Entry(HarvestItemBase):
    def __str__(self):
        # return '%0.02f hours for project %d' % (self.hours, self.project_id)
        return '{:0.2f} hours for project {}'.format(self.hours, self.project.id)

    @property
    def project(self):
        return self.harvest.project(self._project['id'])

    @property
    def task(self):
        return self.harvest.task(self._task['id'])


class UserAssignment(HarvestItemBase):
    def __str__(self):
        return 'user {} for project {}'.format(self.user.id, self.project_id)

    @property
    def project(self):
        return self.harvest.project(self.project_id)

    @property
    def user(self):
        return self.harvest.user(self._user['id'])


class TaskAssignment(HarvestItemBase):
    def __str__(self):
        return 'task {} for project {}'.format(self.task.id, self.project_id)

    @property
    def project(self):
        return self.harvest.project(self.project_id)

    @property
    def task(self):
        return self.harvest.task(self._task['id'])


class Project(HarvestItemBase, metaclass=HarvestItemGetterable):
    base_url = '/projects'
    element_name = 'project'
    plural_name = 'projects'

    def __str__(self):
        return 'Project: ' + self.name

    def entries(self, start=None ,end=None):
        return self.harvest._time_entries(start,
                                          end,
                                          query_params={
                                              'project_id': self.id
                                          })

    @property
    def client(self):
        return self.harvest.client(self.client_id)

    @property
    def task_assignments(self):
        url = '{}/{}/task_assignments'.format(self.base_url, self.id)
        for element in self.harvest._get_element_values(url, 'task_assignments'):
            element['project_id'] = self.id
            yield TaskAssignment(self.harvest, element)

    @property
    def user_assignments(self):
        url = '{}/{}/user_assignments'.format(self.base_url, self.id)
        for element in self.harvest._get_element_values(url, 'user_assignments'):
            element['project_id'] = self.id
            yield UserAssignment(self.harvest, element)


# class User(HarvestItemBase):
class User(HarvestItemBase, metaclass=HarvestItemGetterable):
    base_url = '/people'
    element_name = 'user'
    plural_name = 'users'

    def __str__(self):
        return 'User: {} {}'.format(self.first_name, self.last_name)

    def entries(self, start=None ,end=None):
        return self.harvest._time_entries(start,
                                          end,
                                          query_params={
                                              'user_id': self.id
                                          })
