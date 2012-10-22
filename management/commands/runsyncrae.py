from django.core.management.base import BaseCommand

# optparse AND argparse???
from django.conf import settings
from webdnd.syncrae.config.log import setup as logging_setup
from webdnd.syncrae.websocket import get_app
import argparse
import logging
import tornado.ioloop

def cmdline(args=None, version=''):
    parser = argparse.ArgumentParser(
        prog='Syncrae',
        version='%(prog)s ' + version,
    )

    parser.add_argument(
        '-l', '--log-level',
        dest='SYNCRAE_LOG_LEVEL',
        nargs=1,
        action='store',
        default=False,
        help='Changes the lowest logged level',
        metavar='level',
    )
    parser.add_argument(
        '-f', '--log-file',
        dest='SYNCRAE_LOG_FILE',
        nargs=1,
        action='store',
        default=False,
        help='Selects where to output the logs',
        metavar='file',
    )

    parser.add_argument(
        '-o', '--host', '--open',
        dest='SYNCRAE_HOST',
        action='store_true',
        default=False,
        help='Enables outside hosting (0.0.0.0)',
    )

    # Argument Parsing
    out = parser.parse_args(args)
    return out

class Command(BaseCommand):
    '''
    Removes expired tokens
    '''

    can_import_settings = True

    def run_from_argv(self, argv):
        # Get rid of 'manage.py', 'syncrae'
        argv = argv[2:]
        args = cmdline(args=argv, version=settings.SYNCRAE_VERSION)

        if args.SYNCRAE_LOG_FILE:
            settings.SYNCRAE_LOG_FILE = args.SYNCRAE_LOG_FILE[0]
        level = args.SYNCRAE_LOG_LEVEL
        if level:
            level = level[0]
            try:
                level = int(level)
            except ValueError:
                pass
            settings.SYNCRAE_LOG_LEVEL = level

        settings.SYNCRAE_HOST = '0.0.0.0' if args.SYNCRAE_HOST else '127.0.0.1'

        self.handle()

    def handle(self, *args, **options):
        logging_setup(level=settings.SYNCRAE_LOG_LEVEL)

        self.runserver()


    def runserver(self):
        import tornado.options

        # Intro Message
        import textwrap
        logging.info(textwrap.dedent("""
            Syncrae ~ v%(version)s
                Debug: %(debug)s
                Server is running at http://%(host)s:%(port)s/
                Quit the server with CTRL-C.
        """ % {
            'version': settings.SYNCRAE_VERSION,
            'debug': settings.DEBUG,
            'port': settings.SYNCRAE_PORT,
            'host': settings.SYNCRAE_HOST,
        }))

        get_app({
            'debug': settings.DEBUG,
            'cookie_secret': settings.SECRET_KEY,
            'host': settings.SYNCRAE_HOST,
        }).listen(settings.SYNCRAE_PORT)

        # Allow Ctrl-C to stop the server without the error traceback
        try:
            tornado.ioloop.IOLoop.instance().start()
        except (KeyboardInterrupt, SystemExit):
            tornado.ioloop.IOLoop.instance().stop()
            # Remove the ^C that appears on the same line as your terminal input
            print("")
        finally:
            tornado.ioloop.IOLoop.instance().close()







