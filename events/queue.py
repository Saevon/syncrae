from collections import defaultdict
from syncrae.events.event import Event
from syncrae.utils.decorators import cascade

class CampaignQueue(object):

    queue = {}

    def __init__(self, id):
        self.__listeners = defaultdict(set)
        self.__all = set()
        self.id = id

        CampaignQueue.queue[self.id] = self

    @staticmethod
    def get(id):
        if not id in CampaignQueue.queue.keys():
            return CampaignQueue(id)
        return CampaignQueue.queue[id]

    @staticmethod
    def remove(id):
        if id in CampaignQueue.queue.keys():
            del CampaignQueue.queue[id]

    @cascade
    def write_message(self, topic, data):
        listeners = self.listeners(topic)

        event = Event(topic, data)

        # send message to all listeners
        for listener in listeners:
            event.write_message(listener)

    def listeners(self, topic):
        listeners = set(self.__listeners[topic])
        listeners.update(self.__all)
        return listeners

    @cascade
    def listen(self, obj, topics=True):
        if topics == True:
            self.__all.add(obj)
            return
        for topic in topics:
            self.__listeners[topic].add(obj)

    @cascade
    def drop(self, obj, topics=True):
        self.__all.remove(obj)
        if topics == True:
            return
        for topic in topics:
            self.__listeners[topic].remove(obj)

        if len(self.__all) + len(self.__listeners) == 0:
            CampaignQueue.remove(self.id)

        

