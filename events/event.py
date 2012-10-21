from django.conf import settings
from syncrae.utils.decorators import cascade
import json
import logging

logging = logging.getLogger()

class Event(object):
    topic = None
    data = None

    def __init__(self, topic, data, err=False):
        self.topic = topic
        self.data = data
        self.__json = None

        if not err is False:
            self.data['err_code'] = err
            self.data['err_msg'] = settings.SYNCRAE_ERR_CODES[err]

        logging.info(
            'New Message'
            + ' - < %s >' % self.topic
            + ('' if not err else ' - ERR: < %s > %s' % (
                err, settings.SYNCRAE_ERR_CODES[err]
            ))
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
        except BaseException:
            logging.exception('Error sending message - < %s >' % self.topic)


