from __future__ import print_function

import argparse
import hashlib
import logging
import os.path
import socket
import sys

from earthreader.web import app
from waitress import serve

from libearth.crawler import crawl, CrawlError
from libearth.repository import FileSystemRepository
from libearth.session import Session
from libearth.stage import Stage

__all__ = 'crawl', 'main', 'server'


def crawl_command(args):
    repo = FileSystemRepository(args.repository)
    session = Session()
    stage = Stage(session, repo)
    opml = stage.subscriptions
    if not opml:
        print('OPML does not exist in the repository', file=sys.stderr)
        return
    urllist = [subscription.feed_uri for subscription
               in opml.recursive_subscriptions]
    generator = crawl(urllist, args.threads)
    try:
        for feed_url, (feed_data, crawler_hints) in generator:
            feed_id = hashlib.sha1(feed_url).hexdigest()
            stage.feeds[feed_id] = feed_data
    except CrawlError as e:
        print(e, file=sys.stderr)


def server_command(args):
    repository = args.repository
    if not os.path.isdir(repository):
        os.mkdir(repository)
    app.config.update(REPOSITORY=repository)
    app.debug = args.debug
    if args.debug:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    else:
        serve(app, host=args.host, port=args.port)


parser = argparse.ArgumentParser(prog='earthreader')
subparsers = parser.add_subparsers(dest='command', help='command-help')

server_parser = subparsers.add_parser('server',
                                      help='run a server for Earth Reader')
server_parser.set_defaults(function=server_command)
server_parser.add_argument('-H', '--host',
                           default='0.0.0.0',
                           help="host to listen. [default: %(default)s]")
server_parser.add_argument('-p', '--port',
                           type=int,
                           default=5000,
                           help='port number to listen. [default: %(default)s]')
server_parser.add_argument('-d', '--debug',
                           default=False,
                           action='store_true',
                           help='debug mode. it makes the server possible to '
                                'automatically restart when files touched.')
server_parser.add_argument('repository', help='repository for Earth Reader')

crawl_parser = subparsers.add_parser('crawl', help='crawl feeds in the opml')
crawl_parser.set_defaults(function=crawl_command)
crawl_parser.add_argument('-n', '--threads',
                          type=int,
                          help='the number of workers')
crawl_parser.add_argument('repository', help='repository which has the opml')


def main():
    args = parser.parse_args()
    args.function(args)


if __name__ == '__main__':
    main()
