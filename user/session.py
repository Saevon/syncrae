from django.core.exceptions import ObjectDoesNotExist

from user.models import Game
import datetime


class Session(object):

    def __init__(self):
        self.__game = False
        self.__old = False
        self.__old_expiry = False

    def login(self, key):
        '''
        Logs the user in based on his session id
        Returns the success value (True/False)
        '''
        try:
            self.__game = Game.objects.get(key=key)
        except ObjectDoesNotExist:
            return False

        # If we're successfull, we need a new key
        # TODO: Changing keys laters
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
        if self.__old_expiry and self.__old_expiry + datetime.timedelta(minutes=1) > datetime.datetime.now():
            self.__old_expiry = False
            self.__old = False

    def is_valid(self, key):
        '''
        Returns a boolean that says if your key is correct
        '''
        self.clear_expiry()
        return (
            (
                self.__game
                and self.__game.key == key
            )
            or (
                self.__old
                and self.__old == key
            )
        )

    def new_key(self):
        '''
        Creates a new key
        '''
        # Allow the old key to work for a while
        self.__old = unicode(self.__game.key)
        self.__old_expiry = datetime.datetime.now()

        # Change the actual key
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

