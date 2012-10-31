from collections import defaultdict
from syncrae.events.event import Event
from syncrae.utils.decorators import cascade

class Queue(object):

    queues = {}

    def __init__(self, id):
        self._all = set()
        self.id = id

        # Make sure the factory still works
        self.queues[id] = self

    @classmethod
    def get(cls, id):
        if not id in cls.queues.keys():
            return cls(id)
        return cls.queues[id]

    @classmethod
    def remove(cls, id):
        if id in cls.queues.keys():
            del cls.queues[id]

    @cascade
    def write_message(self, topic, data):
        listeners = self.listeners(topic)

        event = Event(topic, data)

        # send message to all listeners
        for listener in listeners:
            event.write_message(listener)

    def listeners(self, topic):
        listeners = self._all
        return listeners

    @cascade
    def listen(self, obj):
        self._all.add(obj)

    @cascade
    def drop(self, obj):
        self._all.remove(obj)
        if self.is_empty():
            self.remove(self.id)

    def is_empty(self):
        return len(self._all) == 0



class CampaignQueue(Queue):

    queues = {}

    def __init__(self, id):
        super(CampaignQueue, self).__init__(id)
        self._listeners = defaultdict(set)
        self._users = {}

    def listeners(self, topic):
        listeners = super(CampaignQueue, self).listeners(topic)
        listeners.update(set(self._listeners[topic]))
        return listeners

    @cascade
    def listen(self, obj, topics=True):
        self._users[obj.user.id] = obj
        if topics == True:
            super(CampaignQueue, self).listen(obj)
        else:
            for topic in topics:
                self._listeners[topic].add(obj)

    @cascade
    def drop(self, obj, topics=True):
        super(CampaignQueue, self).drop(obj)
        self._users.pop(obj.user.id)
        if topics != True:
            for topic in topics:
                self._listeners[topic].remove(obj)

            if self.is_empty():
                self.remove(self.id)

    def is_empty(self):
        parent = super(CampaignQueue, self).is_empty()
        return (parent and len(self._listeners) == 0)

    def users(self):
        return self._users


class ChatQueue(Queue):
    '''
    A Private chat between n people
    '''

    queues = {}

    def __init__(self, id):
        super(ChatQueue, self).__init__(id)

    @staticmethod
    def id(users):
        ids = list(users)
        ids.sort()
        id = '-'.join([str(id) for id in ids])

        return id

    @cascade
    def listen(self, obj):
        super(ChatQueue, self).listen(obj)
        self.write_message('/chat/open', {
            'chatid': self.id,
            # Uniquify the userids, prevents problems with multiple listeners in a chat
            'users': list(set([u.user.id for u in self._all])),
            'expected': list(set(self.id.split('-'))),
        })

    @cascade
    def drop(self, obj):
        super(ChatQueue, self).drop(obj)
        self.write_message('/chat/close', {
            'chatid': self.id,
        })

class CharacterQueue(Queue):

    queues = {}


