import tornado.ioloop
import tornado.web
import tornado.websocket

from syncrae.events.event import Event
from syncrae.session import Session

from django.conf import settings

from events.queue import CampaignQueue
import logging
import simplejson
import tornado.ioloop
import tornado.web
import tornado.websocket
from django.contrib.auth import get_user
from django.utils.importlib import import_module
from time import time

logging = logging.getLogger('')


class Dummy(object):
    def __init__(self, session):
        self.session = session

class EventWebsocket(tornado.websocket.WebSocketHandler):

    def get_current_user(self):
        engine = import_module(settings.SESSION_ENGINE)
        sessionid = self.get_cookie(settings.SESSION_COOKIE_NAME)

        self.webdnd_session = engine.SessionStore(sessionid)
        request = Dummy(self.webdnd_session)

        return get_user(request)

    def open(self):
        user = self.get_current_user()
        if not user or not user.is_authenticated():
            return self.reject()

        self.user = user
        self.session = Session.get(self.user.id)
        if self.session is None:
            self.session = Session(self)
        else:
            self.session.listen(self)

        self.queue = CampaignQueue.get(self.webdnd_session['cid'])
        self.queue.listen(self)

        # Send the 'New user' event
        self.queue.write_message('/sessions/new', {
            'name':  self.user.name,
        })



    def on_message(self, raw_message):
        try:
            message = simplejson.loads(raw_message)
            topic = message['topic']
            data = message['data']
        except BaseException as err:
            logging.exception('Cannot parse message: %s' % raw_message, err)

        if topic in EventWebsocket.TOPICS.keys():
            if hasattr(self, EventWebsocket.TOPICS[topic]):
                return getattr(self, EventWebsocket.TOPICS[topic])(data)
            else:
                logging.error('Invalid Handler for topic: %s' % topic)
                return
        else:
            # emit event to all listeners
            self.queue.write_message(topic, data)

    def on_close(self):
        self.queue.drop(self)
        self.session.drop(self)

    ##############################################
    # Topic Handlers
    ##############################################

    TOPICS = {
    }

    def reject(self):
        '''
        Occurs when the session is rejected
        '''
        Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        }).write_message(self)
        self.close()


application = None

def get_app(settings):
    global application
    if application is None:
        application = tornado.web.Application([
            # Application URI's
            (r'/event', EventWebsocket),
        ], **settings)

    return application
