# Syncrae Application settings

SYNCRAE_PORT = 8888

SYNCRAE_TORNADO_SETTINGS = {
    'port': SYNCRAE_PORT,
}


SYNCRAE_VERSION = '0.1 BETA'

# Loging info
SYNCRAE_LOG_LEVEL = 'INFO'
SYNCRAE_LOG_FILE = None

# SYNCRAE_ENV_LOCATION = '../../syncrae-env'


# Local settings for Syncrae
try:
    from syncrae.local_settings import *
except ImportError:
    pass

