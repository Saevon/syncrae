import base64
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

# TODO: maybe an easier way to define them...
settings = AttrDict({

    'STATIC_PATH': os.path.join(os.path.dirname(__file__), 'static'),
    'FAVICON_PATH': os.path.join(os.path.dirname(__file__), 'static/img'),
    'DEBUG': True,
    'COOKIE_SECRET': 'syncrae-secret',

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
    },
    'WEBDND_USERNAME': 'syncrae',
    'WEBDND_PASSWORD': 'intra-app[security]0563EA53F521FEAC87B96.syncrae-pass',

    'LOG_LEVEL': 'INFO',
    'LOG_FILE': None,
})


settings['WEBDND_AUTH'] = base64.b64encode(
    '%(username)s:%(password)s' % {
        'username': settings.WEBDND_USERNAME,
        'password': settings.WEBDND_PASSWORD,
    }
)


# provide Tornado settings
TORNADO_SETTINGS = (
    'debug',
    'static_path',
    'cookie_secret',
)
for key in TORNADO_SETTINGS:
    settings[key.lower()] = settings[key.upper()]


# logging settings
import logging
from logutils.colorize import ColorizingStreamHandler

logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

# Customize error colors
# levels to (background, foreground, bold/intense)
ColorizingStreamHandler.level_map = {
    logging.DEBUG: (None, 'blue', False),
    # Use default color for info messages
    logging.INFO: (None, '', False),
    logging.WARNING: (None, 'magenta', False),
    logging.ERROR: (None, 'red', True),
    logging.CRITICAL: ('red', 'white', True),
}

logger.addHandler(ColorizingStreamHandler())


# Update django settings
django_settings.configure(**settings)
