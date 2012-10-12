#!/usr/bin/env python

# Needs to be done first to configure django settings
from settings import settings

from user.session import Session
from events import startup
from events.event import Event
from events.queue import CampaignQueue
import logging
import json
import tornado.ioloop
import tornado.web
import tornado.websocket
import argparse


class EventWebsocket(tornado.websocket.WebSocketHandler):

    def open(self):
        self.session = Session()

        key = self.get_secure_cookie(settings.ID_COOKIE_NAME)
        if not self.session.login(key):
            return self.reject()

        self.queue = CampaignQueue.get(self.session.game.campaign_id).listen(self)

        # Save the new key
        # Which coincidentally doesn't change right now :P
        self.send_key()

        # Send the 'New user' event
        user = startup.user(self)
        self.queue.message('/sessions/new', {
            'name':  user['name'],
        })

    def send_key(self):
        Event('/sessions/key', {
            'key': self.session.key(),
        }).write_message(self)

    def reject(self):
        Event('/sessions/error', {
            'error': 'Your gameplay key was wrong, go back to the campaign and try again.',
        }).write_message(self)
        self.close()

    def on_message(self, raw_message):
        message = json.loads(raw_message)

        # Authentication check
        key = message.get('key')
        if not self.session.is_valid(key):
            return self.reject()

        topic = message.get('topic')
        data = message.get('data')

        # Disabled since you subscribe server side now
        # you can't disable/enable any for now
        # if event.topic == '/subscribe':
            # EventWebsocket.topic_listeners[data].add(self)
            # EventWebsocket.listener_topics[self].add(data)
            # self.write_message(raw_message)
            # return

        # emit event to all listeners
        self.queue.message(topic, data)

    def on_close(self):
        if self.queue:
            self.queue.drop(self)


class ApplicationHandler(tornado.web.RequestHandler):
    def prepare(self):
        pass

    def get(self):
        self.set_secure_cookie(settings.ID_COOKIE_NAME, self.get_argument('key'))

        self.render('application.html')


def cmdline(args=None, version=''):
    parser = argparse.ArgumentParser(
        prog='Syncrae',
        version='%(prog)s ' + version
    )
    subparsers = parser.add_subparsers(dest='COMMAND')

    # Start Server
    parser_runserver = subparsers.add_parser(
        'start',
        description='Starts up the Syncrae Server.'
    )
    parser_runserver.add_argument(
        '-l', '--log-level',
        dest='LOG_LEVEL',
        nargs='?',
        action='store',
        const=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help='Changes the lowest logged level',
        metavar='level'
    )
    parser_runserver.add_argument(
        '-f', '--log-file',
        dest='LOG_FILE',
        nargs='?',
        action='store',
        const=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help='Selects where to output the logs',
        metavar='file'
    )

    # Argument Parsing
    out = parser.parse_args(args)
    return out

def merge_cmdline_settings(settings, args):
    settings.update(args.__dict__)


application = tornado.web.Application([
    # Application URI's
    (r'/play', ApplicationHandler),
    (r'/event', EventWebsocket),
], **settings)

def start():
    # Template handling
    import subprocess
    logging.info('Generating templates')
    subprocess.call(['handlebars', '/apps/syncrae/static/tmpl/', '-f',
        '/apps/syncrae/static/js/templates.js'])
    import os
    logging.debug('  >> %s' % os.stat('/apps/syncrae/static/js/templates.js'))


    # Intro Message
    import textwrap
    print(textwrap.dedent("""
        Syncrae ~ v%(VERSION)s
            Debug: %(DEBUG)s
            Server is running at http://127.0.0.1:%(PORT)s/
            Quit the server with CTRL-C.
    """ % settings))

    application.listen(settings.PORT)

    # Allow Ctrl-C to stop the server without the error traceback
    try:
        tornado.ioloop.IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit) as err:
        tornado.ioloop.IOLoop.instance().stop()
        # Remove the ^C that appears on the same line as your terminal input
        print("")


if __name__ == '__main__':
    merge_cmdline_settings(settings, cmdline())

    commands = {
        'start': start,
    }

    commands[settings.COMMAND]()

