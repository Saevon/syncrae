from utils.decorators import cascade
import json
import logging
import datetime

class Event(object):
    topic = None
    data = None

    def __init__(self, topic, data):
        self.topic = topic
        self.data = data
        self.__json = None

    @property
    def json(self):
        if self.__json is None:
            self.__json = json.dumps({
                'topic': self.topic,
                'data': self.data,
            })
        return self.__json

    @cascade
    def write_message(self, listener):
        try:
            listener.write_message(self.json)
        except BaseException as err:
            logging.error(
                '#### - Error sending message'
                + ' - %s'
                + ' - <' + self.topic + '>'
                + ' - ' + datetime.datetime.now(),
                err,
                exc_info=True
            )


