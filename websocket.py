import tornado.ioloop
import tornado.web
import tornado.websocket

from syncrae.events.event import Event

from django.conf import settings

from events import startup
from events.queue import CampaignQueue
import logging
import simplejson
import tornado.ioloop
import tornado.web
import tornado.websocket



class EventWebsocket(tornado.websocket.WebSocketHandler):

    def open(self):
        sessionid = self.get_cookie(settings.SESSION_COOKIE_NAME)

        # LOGIN
        if login:
            return self.reject()

        self.queue = CampaignQueue.get(self.session.game.campaign_id).listen(self)

        # Save the new key
        # Which coincidentally doesn't change right now :P
        self.send_key()

        # Send the 'New user' event
        user = startup.user(self)
        self.queue.message('/sessions/new', {
            'name':  user['name'],
        })

    def send_key(self):
        Event('/sessions/key', {
            'key': self.session.key(),
        }).write_message(self)

    def reject(self):
        Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        }).write_message(self)
        self.close()

    def on_message(self, raw_message):
        message = simplejson.loads(raw_message)

        # Authentication check
        key = message.get('key')
        if not self.session.is_valid(key):
            return self.reject()

        topic = message.get('topic')
        data = message.get('data')

        # emit event to all listeners
        self.queue.message(topic, data)

    def on_close(self):
        if self.queue:
            self.queue.drop(self)


application = None

def get_app(settings):
    global application
    if application is None:
        application = tornado.web.Application([
            # Application URI's
            (r'/event', EventWebsocket),
        ], **settings)

    return application
