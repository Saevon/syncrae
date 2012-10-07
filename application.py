import os
import json
import logging
from collections import defaultdict
import tornado.ioloop
import tornado.web
import tornado.websocket


from user.session import Session

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
        if not self.session.login(self.get_argument('key')):
            self.reject()

        event = Event('/sessions/new', {
            'key': self.session.key(),
            'name': 'Unknown',
        })

        self._message(event.to_json(),
            EventWebsocket.topic_listeners['/sessions/new'])

    def reject(self):
        # TODO: send a message telling them that their key was rejected
        # then close the connection
        pass

    def on_message(self, raw_message):
        message = json.loads(raw_message)

        # Authentication check
        key = message.get('key')
        if not self.session.is_valid(key):
            return

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
        # import os
        # print os.stat('/apps/dailymeow/static/js/templates.js')
        # import subprocess
        # subprocess.call(['handlebars', '/apps/dailymeow/static/tmpl/', '-f',
            # '/apps/dailymeow/static/js/templates.js'])
        pass

    def get(self):
        self.render('application.html', **{
            'key': self.get_argument('key'),
        })


settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
}

application = tornado.web.Application([
    (r'/play', ApplicationHandler),
    (r'/event', EventWebsocket),
], **settings)


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


