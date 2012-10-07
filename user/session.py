from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

settings.configure(

    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/apps/webdnd/default.sqlite3',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        },
    }

)

from user.models import Game


class Session(object):

    def __init__(self):
        self.__game = False

    def login(self, key):
        '''
        Logs the user in based on his session id
        Returns the success value (True/False)
        '''
        print "----"
        print key
        print [o.key for o in Game.objects.all()]
        try:
            self.__game = Game.objects.get(key=key)
            print self.__game
        except ObjectDoesNotExist:
            return False

        # If we're successfull, we need a new key
        # self.new_key()
        return True

    def logout(self):
        '''
        Logs the user out
        '''
        self.__game.delete()
        self.__game = False

    def clear_expiry(self):
        '''
        Removes any expired keys then logs you back in if your session is
        about to expire.
        '''
        # TODO: add expiry

    def is_valid(self, key):
        '''
        Returns a boolean that says if your key is correct
        '''
        self.clear_expiry()
        return (
            self.__game
            and self.__game.key == key
        )

    def new_key(self):
        '''
        Creates a new key
        '''
        self.__game.new_key()
        self.__game.save()

    def key(self):
        '''
        Returns the current session key
        '''
        if self.__game:
            return self.__game.key
        else:
            return ''

