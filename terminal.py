from django.conf import settings
from syncrae.events.event import Event
from webdnd.player.models.roll import roll_text

import logging
logging = logging.getLogger('')


class Terminal(object):

    def __init__(self, web):
        self.web = web

    def __call__(self, data):
        full_cmd = data.get('cmd')
        cmd = full_cmd.split()

        if len(cmd) == 0:
            return
        elif cmd[0] not in Terminal.COMMANDS.keys():
            Event('/terminal/result', {
                'level': 'error',
                'text': 'Invalid Command: `%s`' % full_cmd,
            }).write_message(self)
            return

        cmd, args = cmd[0], ' '.join([] if len(cmd) <= 1 else cmd[1:])

        # Return the command to the client to state that it was recieved
        Event('/terminal/result', {
            'cmd': True,
            'level': 'cmd',
            'text': full_cmd,
        }).write_message(self)

        # only log accepted commands
        logging.info('New Command - %s' % full_cmd)

        handler = 'term_' + Terminal.COMMANDS[cmd]['handler']
        if hasattr(self, handler):
            getattr(self, handler)(args)
            return
        else:
            logging.error('Invalid Handler for cmd: < %s > - %s:%s' % (self.__full, full_cmd, handler))
            return

    def write_message(self, json):
        self.web.write_message(json)

    def start(self):
        pass

    def terminal_write(self, text, level='info', err=False):
        Event('/terminal/result', {
            'level': level,
            'text': text or ' ',  # &nbsp;
        }, err=err).write_message(self)

    def terminal_err(self, err, level=None):
        data = {}
        if not level is None:
            data['level'] = level

        Event('/terminal/error', data, err=err).write_message(self)

    ##############################################
    # Actual commands
    ##############################################

    COMMANDS = {
        'colors': {
            'handler': 'color_test',
        },
        'echo': {
            'handler': 'echo',
        },
        'error': {
            'handler': 'error',
        },
        'roll': {
            'handler': 'roll',
        }
    }

    def term_color_test(self, cmd):
        self.terminal_write('Color Test:')

        levels = ['cmd', 'normal', 'info', 'warn', 'error', 'critical', 'muted']

        for level in levels:
            self.terminal_write(level=level, text=" >> %s" % level)

    def term_echo(self, cmd):
        self.terminal_write(cmd, level='normal')

    def term_error(self, cmd):
        if len(cmd) > 1 and cmd in settings.SYNCRAE_ERR_CODES:
            self.terminal_err(level='error', err=cmd)
        else:
            self.terminal_write('Invalid err code.', level='error')

    def term_roll(self, cmd):
        self.terminal_write(roll_text(cmd))
