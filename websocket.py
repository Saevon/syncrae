from django.conf import settings
from django.contrib.auth import get_user
from django.utils.importlib import import_module

from events.queue import CampaignQueue
from functools import wraps
from syncrae.events.event import Event
from syncrae.session import Session
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

        self.queue = CampaignQueue.get(self.webdnd_session['cid'])
        self.queue.listen(self)

        # Send the 'New user' event
        self.queue.write_message('/sessions/status', {
            'name':  self.user.name,
            'status': 'online',
        })

    def on_close(self):
        if self.session is not None:
            self.session.drop(self)

        if self.queue is not None:
            self.queue.drop(self)
            # Make sure the campaign group knows you logged out
            self.queue.write_message('/sessions/status', {
                'name': self.user.name,
                'status': 'offline',
            })

    def on_message(self, raw_message):
        try:
            message = simplejson.loads(raw_message)
            topic = message['topic']
            data = message['data']
        except BaseException:
            logging.exception('Cannot parse message: ' + raw_message)

        self.handle_topic(topic, data)


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
        '/terminal/command': 'terminal',
    }

    def reject(self):
        '''
        Occurs when the session is rejected
        '''
        Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        }).write_message(self)
        self.close()

    def hdl_default(self, topic, data):
        # emit event to all listeners
        # using the original full topic
        self.queue.write_message(topic, data)

    def hdl_message(self, data):
        data['name'] = self.user.name

    def hdl_terminal(self, data):
        full_cmd = data.get('cmd')
        cmd = full_cmd.split()
        cmd, args = cmd[0], ' '.join(cmd[1:])

        if cmd is None:
            return
        elif cmd not in EventWebsocket.COMMANDS.keys():
            Event('/terminal/result', {
                'level': 'error',
                'log': 'Invalid Command: `%s`' % full_cmd,
            }).write_message(self)
            return

        # Return the command to the client to state that it was recieved
        Event('/terminal/result', {
            'cmd': True,
            'level': 'cmd',
            'log': full_cmd,
        }).write_message(self)

        # only log accepted commands
        logging.info('New Command - %s' % full_cmd)

        handler = 'term_' + EventWebsocket.COMMANDS[cmd]['handler']
        if hasattr(self, handler):
            getattr(self, handler)(args)
            return
        else:
            logging.error('Invalid Handler for cmd: < %s > - %s:%s' % (self.__full, full_cmd, handler))
            return

    ##############################################
    # Terminal
    ##############################################

    COMMANDS = {
        'colors': {
            'handler': 'color_test',
        },
        'echo': {
            'handler': 'echo',
        }
    }

    def terminal_write(self, log, level='info'):
        Event('/terminal/result', {
            'level': level,
            'log': log or ' ',  # &nbsp;
        }).write_message(self)

    def term_color_test(self, cmd):
        self.terminal_write('Color Test:')

        levels = ['cmd', 'normal', 'info', 'warn', 'error', 'critical', 'muted']

        for level in levels:
            self.terminal_write(level=level, log=" >> %s" % level)

    def term_echo(self, cmd):
        self.terminal_write(cmd, level='normal')


application = None

def get_app(settings):
    global application
    if application is None:
        application = tornado.web.Application([
            # Application URI's
            (r'/event', EventWebsocket),
        ], **settings)

    return application
