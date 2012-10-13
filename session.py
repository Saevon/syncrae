import logging
logging = logging.getLogger()


class Session(object):
    '''
    Persists a session across tabs, so you can have multiple websockets
    across different browsers/tabs etc.
    '''

    all = {}

    STATUSES = {
        'on': 'Online',
        'off': 'Offline',
    }

    def __init__(self, listener):
        self.user = listener.user
        self.status = 'off'

        self.listeners = set()
        self.listen(listener)

        Session.all[self.user.id] = self
        self.id = self.user.id

        logging.info('New Session - %s %s' % (self.user.id, self.user.name))

    @staticmethod
    def get(uid):
        return Session.all.get(uid)

    @staticmethod
    def remove(uid):
        s = Session.get(uid)
        if s is None:
            return
        s.set_status('off')

        logging.info('Logged Out - %s %s' % (s.user.id, s.user.name))

    def set_status(self, status):
        self.status = status

    def write_message(self, event):
        '''
        Gives a message to every open window for this session
        '''
        for l in self.listeners:
            event.write_message(l)

    def listen(self, listener):
        if self.status == 'off':
            self.set_status('on')
        self.listeners.add(listener)

    def drop(self, listener):
        self.listeners.discard(listener)
        if len(self.listeners) == 0:
            Session.remove(self.id)

    @property
    def json(self):
        return {
            'id': self.user.id,
            'name': self.user.name,
            'status': Session.STATUSES[self.status],
        }



