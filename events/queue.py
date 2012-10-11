from collections import defaultdict
from events.event import Event
from utils.decorators import cascade

class CampaignQueue(object):

    queue = {}

    def __init__(self):
        self.__listeners = defaultdict(set)
        self.__all = set()

    @cascade
    def message(self, topic, data):
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

    @staticmethod
    def get(id):
        if not id in CampaignQueue.queue.keys():
            CampaignQueue.queue[id] = CampaignQueue()
        return CampaignQueue.queue[id]

    @staticmethod
    def playing():
        return CampaignQueue.queue.keys()

        

