from collections import defaultdict
from syncrae.events.event import Event
from syncrae.utils.decorators import cascade

class Queue(object):

    queues = {}

    def __init__(self, id):
        self.__all = set()
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
        listeners = self.__all
        return listeners

    @cascade
    def listen(self, obj):
        self.__all.add(obj)

    @cascade
    def drop(self, obj):
        self.__all.remove(obj)
        if self.is_empty():
            self.remove(self.id)

    def is_empty(self):
        return len(self.__all) == 0



class CampaignQueue(Queue):

    queues = {}

    def __init__(self, id):
        super(CampaignQueue, self).__init__(id)
        self.__listeners = defaultdict(set)
        self.__users = {}

    def listeners(self, topic):
        listeners = super(CampaignQueue, self).listeners(topic)
        listeners.update(set(self.__listeners[topic]))
        return listeners

    @cascade
    def listen(self, obj, topics=True):
        self.__users[obj.user.id] = obj
        if topics == True:
            super(CampaignQueue, self).listen(obj)
        else:
            for topic in topics:
                self.__listeners[topic].add(obj)

    @cascade
    def drop(self, obj, topics=True):
        super(CampaignQueue, self).drop(obj)
        self.__users.pop(obj.user.id)
        if topics != True:
            for topic in topics:
                self.__listeners[topic].remove(obj)

            if self.is_empty():
                self.remove(self.id)

    def is_empty(self):
        parent = super(CampaignQueue, self).is_empty()
        return (parent and len(self.__listeners) == 0)

    def users(self):
        return self.__users


class ChatQueue(Queue):
    '''
    A Private chat between n people
    '''

    queues = {}

    def __init__(self, users):
        id = ChatQueue.id(users)
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
            'id': self.id,
        })

    @cascade
    def drop(self, obj):
        super(ChatQueue, self).drop(obj)
        self.write_message('/chat/open', {
            'id': self.id,
        })


