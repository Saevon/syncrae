from django.core.management.base import BaseCommand

# optparse AND argparse???
from django.conf import settings
from optparse import make_option
import argparse

class Command(BaseCommand):
    '''
    Removes expired tokens
    '''

    option_list = BaseCommand.option_list + (
        make_option('-l', '--log-level',
            dest='SYNCRAE_LOG_LEVEL',
            nargs=1,
            action='store',
            default=argparse.SUPPRESS,
            help='Changes the lowest logged level',
            metavar='level'
        ),
        make_option('-f', '--log-file',
            dest='SYNCRAE_LOG_FILE',
            nargs=1,
            action='store',
            default=argparse.SUPPRESS,
            help='Selects where to output the logs',
            metavar='file'
        ),
        make_option('-e', '--env',
            dest='SYNCRAE_ENV_LOCATION',
            nargs='?',
            action='store',
            # const='../syncrae-env',
            default=argparse.SUPPRESS,
            help='The environment to use to run the Sycrae server.',
            metavar='location'
        ),
    )

    def handle(self, *args, **options):
        for key in options.keys():
            if options[key] != argparse.SUPPRESS:
                settings.__setattr__(key, options[key])

