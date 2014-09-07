""":mod:`earthreader.web.command` --- Command interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function

import argparse
import os
import sys

from libearth.session import Session
from six.moves import urllib
from waitress import serve

from . import app


def server_command(args):
    repository = args.repository
    app.config.update(REPOSITORY=repository, SESSION_ID=args.session_id)
    app.debug = args.debug
    if args.profile:
        try:
            from linesman.middleware import make_linesman_middleware
        except ImportError:
            print('-P/--profile/--linesman option is available only when '
                  "linesman is installed", file=sys.stderr)
            print('Try the following command:', file=sys.stderr)
            print('\tpip install linesman', file=sys.stderr)
            raise SystemExit
        else:
            print('Profiler (linesman) is available:',
                  'http://{0.host}:{0.port}/__profiler__/'.format(args))
        app.wsgi_app = make_linesman_middleware(app.wsgi_app)
    if args.debug:
        app.run(host=args.host, port=args.port, debug=args.debug,
                threaded=True)
    else:
        serve(app, host=args.host, port=args.port)


parser = argparse.ArgumentParser(prog='earthreader')
subparsers = parser.add_subparsers(dest='command')
server_parser = subparsers.add_parser('server', help='Start EarthReader-Web')
server_parser.set_defaults(function=server_command)
server_parser.add_argument('-H', '--host', default='0.0.0.0',
                           help="Host to listen. [default: %(default)s]")
server_parser.add_argument('-p', '--port', type=int, default=5000,
                           help='Port number to listen. [default: %(default)s]')
server_parser.add_argument('-d', '--debug', default=False, action='store_true',
                           help='debug mode. Automatically restart the server'
                                'when files are changed.')
server_parser.add_argument('-i', '--session-id', default=Session().identifier,
                           help='Session identifier. [default: %(default)s]')
server_parser.add_argument('-P', '--profile', '--linesman',
                           default=False, action='store_true',
                           help="Profile using linesman. Available only "
                                'when linesman is installed.')
server_parser.add_argument('repository', help='Earth Reader repository.')


def cli():
    args = parser.parse_args()
    url = urllib.parse.urlparse(args.repository)
    if not url.scheme:
        url = urllib.parse.urljoin('file://',
                                   os.path.join(os.getcwd(), args.repository))
    if args.command:
        args.repository = url
        args.function(args)
    else:
        parser.print_help()
