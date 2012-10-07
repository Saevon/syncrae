from django.contrib.auth.models import User
from django.db import models

import random
import string


KEY_LENGTH = 64

class Game(models.Model):

    ALLOWED_CHARS = string.ascii_letters + string.digits + '~!@$%^*()_-,.:|{}[]'

    class Meta:
        app_label = 'player'
        unique_together = ('user', 'campaign')

    user = models.OneToOneField(
        User,
        related_name='game',
        blank=False,
        null=False
    )
    campaign_id = models.IntegerField(
        blank=False,
        null=False
    )
    key = models.CharField(
        max_length=KEY_LENGTH,
        blank=False,
        null=True
    )

    def new_key(self):
        '''
        Creates a new key for this Game, you still need to save() afterwards
            Note: This can be a different method from the Django App one.
        '''
        self.key = ''.join([random.choice(Game.ALLOWED_CHARS) for i in range(KEY_LENGTH)])

