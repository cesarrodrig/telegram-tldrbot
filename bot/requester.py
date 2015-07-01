import requests
import json

import logger
from config import *

# Credits to @ixai for this Requester model

class Encoder(json.JSONEncoder):
    def default(self, o):
        return {k:o.__dict__[k] for k in o.__dict__ if o.__dict__[k] != None}

class Requester(object):
    def __init__(self, url, request_path, query_params, request_body=None):
        self.__url = "%s%s" % (url, request_path)
        self.__query_params = query_params
        self.__request_body = request_body
        self.logger = logger.get_logger(__name__)

    def __query(self):
        r = reduce(lambda x,y: "%s%s=%s&" % (x,y,self.__query_params[y]), self.__query_params, "")
        return r

    def _post(self):
        data = json.dumps(self.__request_body, cls=Encoder)
        self.logger.info("POST %s?%s\n%s" % (self.__url, self.__query(), data))
        r = requests.post(self.__url, params=self.__query_params, data=data)
        b = r.text
        if b == "":
            b = "{}"
        self.logger.info("Response: %s" % (b))
        return (r, json.loads(b))

    def _get(self):
        self.logger.info("GET %s?%s" % (self.__url, self.__query()))
        r = requests.get(self.__url, params=self.__query_params)
        b = r.text
        if b == "":
            b = "{}"
        self.logger.info("Response: %s" % (b))
        return (r, json.loads(b))

    def _delete(self):
        self.logger.info("DELETE %s?%s" % (self.__url, self.__query()))
        r = requests.delete(self.__url, params=self.__query_params)
        b = r.text
        if b == "":
            b = "{}"
        self.logger.info("Response: %s" % (b))
        return (r, json.loads(b))

class TlDrRequester(Requester):

    def __init__(self, request_path, query_params, request_body=None):
        super(TlDrRequester, self).__init__(BOT_URL, request_path, query_params, request_body)

class SetWebhookRequest(TlDrRequester):
    """
    POST /setWebhook
    """
    def __init__(self, url=""):
        request_path = '/setWebhook'
        request_body = {}
        query_params = {
            "url": url
        }
        super(SetWebhookRequest, self).__init__(request_path, query_params, request_body)

    def do(self):
        return self._post()

class GetUpdatesRequest(TlDrRequester):
    """
    GET /getUpdates
    """
    def __init__(self, offset=0, limit=100, timeout=0):
        request_path = '/getUpdates'
        request_body = {}
        query_params = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout
        }
        super(GetUpdatesRequest, self).__init__(request_path, query_params, request_body)

    def do(self):
        return self._get()

class SendMessageRequest(TlDrRequester):
    """
    GET /sendMessage
    """
    def __init__(self, chat_id, text, extra_query_params={}):
        request_path = '/sendMessage'
        request_body = {}
        query_params = {
            "chat_id": chat_id,
            "text": text
        }
        extra_query_params.update(query_params)
        super(SendMessageRequest, self).__init__(request_path, extra_query_params, request_body)

    def do(self):
        return self._get()
