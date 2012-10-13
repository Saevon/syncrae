from logutils.colorize import ColorizingStreamHandler
import logging


# Customize error colors
# levels to (background, foreground, bold/intense)
ColorizingStreamHandler.level_map = {
    logging.DEBUG: (None, 'cyan', False),
    # Use default color for info messages
    logging.INFO: (None, '', False),
    logging.WARNING: (None, 'magenta', False),
    logging.ERROR: (None, 'red', True),
    logging.CRITICAL: ('red', 'white', True),
}


def setup(level=None):
    logger = logging.getLogger()

    # disable all other handlers
    for h in logger.handlers:
        logger.removeHandler(h)

    if isinstance(level, basestring):
        level = level.upper()

    if level:
        try:
            logger.setLevel(level)
        except TypeError as err:
            # Logging here actually doesn't work ??
            # logger.warn('Bad Log level was passed in %(err)s', err)
            # Bad log level passed in
            pass

    logger.addHandler(ColorizingStreamHandler())

