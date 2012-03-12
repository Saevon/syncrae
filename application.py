import os
import json
import logging
from collections import defaultdict
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
                logging.error('Error sending message', exc_info=True)

    def open(self):
        event = Event('/sessions/new', {'id': 'randomid'})
        self._message(event.to_json(),
            EventWebsocket.topic_listeners['/sessions/new'])

    def on_message(self, raw_message):
        message = json.loads(raw_message)
        topic = message['topic']
        data = message['data']
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
        import subprocess
        subprocess.call(['handlebars', '/apps/dailymeow/static/tmpl/', '-f',
            '/apps/dailymeow/static/js/templates.js'])

    def get(self):
        self.render('application.html')


settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
}

application = tornado.web.Application([
    (r'/', ApplicationHandler),
    (r'/e', EventWebsocket),
], **settings)


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


# ideas...
import redis
redis = redis.StrictRedis(host='localhost', port=6379, db=0)


class Resource:
    def _namespace(cls):
        return cls.__name__.lower()

    def _id(cls, _id):
        return '%s:%s' % (cls.__name__.lower(), _id)

    @classmethod
    def create(cls, data, listeners):
        if not 'id' in data:
            data['id'] = redis.incr('global:%s' % cls._namespace())
        _id = cls._id(data['id'])
        redis.set(_id, data)
        redis.lpush(cls._namespace(), _id)
        return data, listeners

    @classmethod
    def update(cls, data, listeners):
        redis.set(cls._id(data['id']), data)
        return data, listeners

    @classmethod
    def delete(cls, data, listeners):
        return redis.delete(cls._id(data['id'])), listeners

    @classmethod
    def read(cls, data, listeners):
        return redis.get(cls._id(data['id'])), set([])

    @classmethod
    def list(cls, listeners):
        ids = redis.get(cls._namespace())
        collection = []
        for _id in ids:
            collection.append(redis.get(_id))
        return collection, set([])
