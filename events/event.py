from syncrae.utils.decorators import cascade
import json
import logging

class Event(object):
    topic = None
    data = None

    def __init__(self, topic, data):
        self.topic = topic
        self.data = data
        self.__json = None

        logging.info(
            'New Message'
            + ' - < ' + self.topic + ' >'
        )

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
            logging.exception(
                '#### - Error sending message'
                + ' - %s'
                + ' - < ' + self.topic + ' >',
                err
            )


