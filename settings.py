import os
from django.conf import settings as django_settings

class AttrDict(dict):
    '''
    Provides Attribute access to a dict object
      Used to allow django settings like access
    '''
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

settings = AttrDict({

    'STATIC_PATH': os.path.join(os.path.dirname(__file__), 'static'),
    'FAVICON_PATH': os.path.join(os.path.dirname(__file__), 'static/img'),
    'DEBUG': True,
    'cookie_secret': 'syncrae-secret',

    'ID_COOKIE_NAME': 'webdnd_playid',

    'PORT': 8888,

    'VERSION': '0.0',
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/apps/webdnd/default.sqlite3',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        },
    }
})


# provide Tornado settings (non caps)
settings.debug = settings.DEBUG
settings.static_path = settings.STATIC_PATH

# Update django settings
django_settings.configure(**settings)
