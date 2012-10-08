# Needs to be done first to configure django settings
from settings import settings

from collections import defaultdict
from user.session import Session
import json
import logging
import os
import tornado.ioloop
import tornado.web
import tornado.websocket



class Event(object):
    topic = None
    data = None

    def __init__(self, topic, data):
        self.topic = topic
        self.data = data

    def to_json(self):
        return json.dumps({
            'topic': self.topic,
            'data': self.data,
        })

class EventWebsocket(tornado.websocket.WebSocketHandler):
    listener_topics = defaultdict(set)
    topic_listeners = defaultdict(set)
    user = None

    def _message(self, message, listeners):
        # event creator always receives echo of their event
        listeners.add(self)

        # send message to all listeners
        for listener in listeners:
            try:
                listener.write_message(message)
            except:
                logging.error('Error sending message: ' + message, exc_info=True)

    def open(self):
        self.session = Session()

        key = self.get_secure_cookie(settings.ID_COOKIE_NAME)
        if not self.session.login(key):
            return self.reject()

        # Save the new key
        # Which coincidentally doesn't change right now :P
        self.send_key()

        # Send the 'New user' event
        event = Event('/sessions/new', {
            'name': 'Unknown',
        })

        self._message(event.to_json(),
            EventWebsocket.topic_listeners['/sessions/new'])

    def send_key(self):
        event = Event('/sessions/key', {
            'key': self.session.key(),
        })

        self.write_message(event.to_json())

    def reject(self):
        event = Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        })
        self.write_message(event.to_json())
        self.close()

    def on_message(self, raw_message):
        message = json.loads(raw_message)

        # Authentication check
        key = message.get('key')
        if not self.session.is_valid(key):
            return self.reject()

        topic = message.get('topic')
        data = message.get('data')

        if topic == '/subscribe':
            EventWebsocket.topic_listeners[data].add(self)
            EventWebsocket.listener_topics[self].add(data)
            self.write_message(raw_message)
            return

        # echo event back
        listeners = EventWebsocket.topic_listeners[topic]
        event = Event(topic, data)

        # emit event to all listeners
        self._message(event.to_json(), listeners)

    def on_close(self):
        for topic in EventWebsocket.listener_topics[self]:
            EventWebsocket.topic_listeners[topic].remove(self)
            if len(EventWebsocket.topic_listeners[topic]) == 0:
                del EventWebsocket.topic_listeners[topic]
        del EventWebsocket.listener_topics[self]


class ApplicationHandler(tornado.web.RequestHandler):
    def prepare(self):
        # this should be for debug mode only...
        # render mustache templates
        # Perhaps this should happen on server load?
        # Not per request to the page
        print os.stat('/apps/syncrae/static/js/templates.js')

        import subprocess
        subprocess.call(['handlebars', '/apps/syncrae/static/tmpl/', '-f',
            '/apps/syncrae/static/js/templates.js'])

    def get(self):
        self.set_secure_cookie('webdnd_playid', self.get_argument('key'))

        self.render('application.html')


application = tornado.web.Application([
    # Application URI's
    (r'/play', ApplicationHandler),
    (r'/event', EventWebsocket),
], **settings)


if __name__ == '__main__':
    import textwrap
    print textwrap.dedent("""
        Syncrae ~ v%(VERSION)s
            Debug: %(DEBUG)s
            Server is running at http://127.0.0.1:%(PORT)s/
            Quit the server with CTRL-C.
    """ % settings)

    application.listen(settings.PORT)

    # Allow Ctrl-C to stop the server without the error traceback
    try:
        tornado.ioloop.IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        tornado.ioloop.IOLoop.instance().stop()
        # Remove the ^C that appears on the same line as your terminal input
        print ""

