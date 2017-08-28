import json
import sys
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session

class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class CyreneClient:
    def __init__(self, cyreneHost, oauth2clientId, oauth2clientSecret):
        # host without prefix and without trailing slash
        if 'http://' in cyreneHost or 'https://' in cyreneHost:
            raise InputError(cyreneHost, 'no http or https prefix for cyreneHost allowed. https is used automatically.')
        if cyreneHost == '':
            raise InputError(cyreneHost, 'cyreneHost is empty.')
        if oauth2clientId == '':
            raise InputError(oauth2clientId, 'oauth2clientId is empty.')
        if oauth2clientSecret == '':
            raise InputError(oauth2clientSecret, 'oauth2clientSecret is empty.')

        self.host = cyreneHost
        self.clientId = oauth2clientId
        self.clientSecret = oauth2clientSecret
        self.token = None

    def get(self, relativePath):
        return json.loads(self.simple_action('get', relativePath))

    def delete(self, relativePath):
        return json.loads(self.simple_action('delete', relativePath))

    def post(self, relativePath, dataDict):
        return json.loads(self.data_action('post', relativePath, dataDict))

    def patch(self, relativePath, dataDict):
        return json.loads(self.data_action('patch', relativePath, dataDict))

    def put(self, relativePath, dataDict):
        return json.loads(self.data_action('put', relativePath, dataDict))

    def get_model_list(self, clientName, spaceId = 0):
        return self.get(clientName + '/' + str(spaceId) + '/Models')

    def data_action(self, action, relativePath, dataDict):
        # relativePath should begin with a slash
        if not relativePath.startswith('/'):
            raise InputError(relativePath, 'relativePath should begin with a slash.')
        if len(dataDict) == 0:
            raise InputError(dataDict, 'dataDict is empty, nothing to post.')

        if self.token is None:
            self.acquire_token()

        headerDict = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        url = 'https://' + self.host + relativePath
        client = OAuth2Session(self.clientId, token=self.token)

        try:
            if action == 'post':
                r = client.post(url, None, dataDict, headers=headerDict)
            elif action == 'put':
                r = client.put(url, json.dumps(dataDict), headers=headerDict)
            elif action == 'patch':
                r = client.patch(url, json.dumps(dataDict), headers=headerDict)
            else:
                raise InputError(action, 'unknown action')
        except TokenExpiredError:
            self.token = None
            return self.data_action(action, relativePath, dataDict)

        return r.content.decode('utf-8')

    def getClientDoc(self):
        return self.get('/REST/clientDoc')

    def simple_action(self, action, relativePath):
        # relativePath should begin with a slash
        if not relativePath.startswith('/'):
            raise InputError(relativePath, 'relativePath should begin with a slash.')

        if self.token is None:
            self.acquire_token()
        headerDict = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        url = 'https://' + self.host + relativePath
        client = OAuth2Session(self.clientId, token=self.token)

        try:
            if action == 'get':
                r = client.get(url, headers=headerDict)
            elif action == 'delete':
                r = client.delete(url, headers=headerDict)
            else:
                raise InputError(action, 'unknown action')
            return r.content.decode('utf-8')
        except TokenExpiredError:
            self.token = None
            return self.simple_action(action, relativePath)

    def acquire_token(self):
        token_url = 'https://' + self.host + '/oauth2/token'
        client = BackendApplicationClient(client_id=self.clientId)
        oauth = OAuth2Session(client=client)
        self.token = oauth.fetch_token(token_url=token_url, client_id=self.clientId, client_secret=self.clientSecret)

if __name__ == "__main__":
    c = CyreneClient('lrx.cyrene.io', 'cyrene_dev_client', 'CYRENE_DEV_CLIENT_SECRET')
    #space = 'Main'
    #model = sys.argv[1]
    #relPath = '/' + space + '/' + model
    #r = c.get(relPath)

    booking = {
        'name': 'Max Mustermann',
        'event': 'magnum',
        'email': 'max@mustermann.com',
        'phone': '0761/13234',
        'groupsize': 5,
        'timestamp': ['13:30','23.5.2017'],
        'start': ['14:30','24.5.2017'],
        'end': ['16:30','24.5.2017']
    }

    relPath = '/Main/Bookings'
    parsed = c.post(relPath, booking)
    print(json.dumps(parsed, indent=2, sort_keys=True))
