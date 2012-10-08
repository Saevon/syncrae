import json

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

