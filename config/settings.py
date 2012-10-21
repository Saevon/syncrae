# Syncrae Application settings

SYNCRAE_PORT = 8888

SYNCRAE_TORNADO_SETTINGS = {
    'port': SYNCRAE_PORT,
}


# format: 'major.minor.bug name'
SYNCRAE_VERSION = '0.1.0 BETA'

# Loging info
SYNCRAE_LOG_LEVEL = 'INFO'
SYNCRAE_LOG_FILE = None

# SYNCRAE_ENV_LOCATION = '../../syncrae-env'


SYNCRAE_ERR_CODES = {
    # All err codes start with a '5' to represent Syncrae
    # And are a 4 digit number
    # Digit two represents one of the following groups
    # The remaining two digits are a simple unique identifier

    # 1: User error
    '5101': 'Not Logged In',

}

# Local settings for Syncrae
try:
    from syncrae.local_settings import *
except ImportError:
    pass

