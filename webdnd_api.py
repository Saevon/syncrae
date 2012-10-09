from settings import settings
from utils.decorators import cascade
import logging
import simplejson
import urllib
import urllib2

class Api(object):

    WEBDND = 'localhost:9000'

    def __init__(self, key, endpoint, data=None):
        self.__key = key
        self.__endpoint = endpoint
        self.__error = False
        self.request(data)

    @cascade
    def request(self, data=None):
        if data is None:
            data = {}
        data['key'] = self.__key

        headers = {
            'AUTHORIZATION': 'Basic %s' % settings.WEBDND_AUTH,
        }

        url_values = urllib.urlencode(data)
        req = urllib2.Request('http://%(WEBDND)s/api/%(endpoint)s?%(url_values)s' % {
            'WEBDND': Api.WEBDND,
            'endpoint': self.__endpoint,
            'url_values': url_values,
        }, headers=headers)

        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, err:
            # HTTP Error
            self._error(code=err.code, text=err.msg)
        except urllib2.URLError, err:
            # Failed to Reach the Server
            self._error(text=err.reason[1], code=err.reason[0])
        else:
            out = response.read()
            try:
                self.__response = simplejson.loads(out)
            except simplejson.JSONDecodeError:
                self._error(text='JSON Decode Error')

    def _error(self, code=0, text=''):
        self.__error = True
        self.__response = {
            'errors': [{
                'code': code,
                'text': text,
                'location': self.__endpoint,
            }]
        }

    @property
    def has_error(self):
        if self.__error:
            logging.error(self.errors)
        return self.__error

    @property
    def errors(self):
        return self.__response['errors']

    @property
    def response(self):
        return self.__response['output']

    @property
    def paging(self):
        return self.__response['paging']









