from django.conf import settings
from django.contrib.auth import get_user
from django.utils.importlib import import_module

from webdnd.player.models.roll import roll_text
from webdnd.player.models.campaigns import Campaign

from events.queue import CampaignQueue, ChatQueue, CharacterQueue
from functools import wraps
from syncrae.events.event import Event
from syncrae.session import Session
from syncrae.terminal import Terminal
import logging
import simplejson
import tornado.ioloop
import tornado.web
import tornado.websocket

logging = logging.getLogger('')


class RequestDummy(object):
    def __init__(self, session):
        self.session = session

class EventWebsocket(tornado.websocket.WebSocketHandler):

    def async(self, func, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        # wraps the function to pass the given args
        @wraps(func)
        def wrapper():
            return func(*args, **kwargs)

        # Use tornado's async timer, set to now
        tornado.ioloop.IOLoop.instance().add_callback(wrapper)

    def get_current_user(self):
        engine = import_module(settings.SESSION_ENGINE)
        sessionid = self.get_cookie(settings.SESSION_COOKIE_NAME)

        self.webdnd_session = engine.SessionStore(sessionid)
        request = RequestDummy(self.webdnd_session)

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

        cid = self.webdnd_session['cid']
        self.campaign = Campaign.objects.get(id=cid)

        self.queue = CampaignQueue.get(cid)
        self.queue.listen(self)

        self.chats = set()
        for userid in self.queue.users().keys():
            if userid != self.user.id:
                self.new_chat(userid)

        # Send the 'New user' event
        self.queue.write_message('/sessions/status', {
            'name':  self.user.name,
            'status': 'online',
        })

        self.terminal = Terminal(self)
        self.async(self.terminal.start)

    def on_close(self):
        if hasattr(self, 'session') and not self.session is None:
            self.session.drop(self)

        if hasattr(self, 'queue') and not self.queue is None:
            self.queue.drop(self)
            # Make sure the campaign group knows you logged out
            self.queue.write_message('/sessions/status', {
                'name': self.user.name,
                'status': 'offline',
            })

        if hasattr(self, 'chats') and not self.chats is None:
            for chat in self.chats:
                chat.drop(self)

    def on_message(self, raw_message):
        try:
            message = simplejson.loads(raw_message)
            topic = message['topic']
            data = message['data']
        except BaseException:
            logging.exception('Cannot parse message: ' + raw_message)

        self.handle_topic(topic, data)

    def new_chat(self, id):
        id = ChatQueue.id([self.user.id, id])
        chat = ChatQueue.get(id)

        self.chats.add(chat)

        chat.listen(self)


    ##############################################
    # Topic Handling Code
    ##############################################
    def handle_topic(self, topic, data):
        self.__full = topic

        topic = topic.strip().strip('/')
        parts = topic.split('/')

        # call every base handler
        for l in range(len(parts) - 1):
            sub_topic = '/%s' % '/'.join(parts[:l + 1])
            self.call(sub_topic, data)

        # Final Handler is special, this is the one that actually counts
        # if it fails we use the default handler
        if not self.call(self.__full, data):
            self.hdl_default(self.__full, data)

    def call(self, topic, data):
        '''
        calls the relevant handler
        '''
        if not topic in EventWebsocket.TOPICS.keys():
            return False

        handler = 'hdl_' + EventWebsocket.TOPICS[topic]
        if hasattr(self, handler):
            getattr(self, handler)(data)
            return True
        else:
            logging.error('Invalid Handler for topic: < %s > - %s:%s' % (self.__full, topic, handler))
            return False


    ##############################################
    # Topic Handlers
    ##############################################

    TOPICS = {
        '/messages': 'message',
        '/messages/new': 'msg_new',
        '/terminal/command': 'terminal',
    }

    def reject(self):
        '''
        Occurs when the session is rejected
        '''
        Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        }, err='5101').write_message(self)
        self.close()

    def hdl_default(self, topic, data):
        # emit event to all listeners
        # using the original full topic
        self.queue.write_message(topic, data)

    def hdl_msg_new(self, data):
        chatid = data.get('chatid')
        if chatid and chatid != 'campaign':
            ChatQueue.get(chatid).write_message('/messages/new', data)
        else:
            data['chatid'] = 'campaign'
            self.hdl_default('/messages/new', data)

    def hdl_message(self, data):
        data['name'] = self.user.name
        data['msg'] = roll_text(data['msg'])

    def hdl_terminal(self, data):
        return self.terminal(data)

application = None

def get_app(settings):
    global application
    if application is None:
        application = tornado.web.Application([
            # Application URI's
            (r'/event', EventWebsocket),
        ], **settings)

    return application
