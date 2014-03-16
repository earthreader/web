from __future__ import print_function

import argparse
import os
import sys
import traceback
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

from libearth.compat.parallel import cpu_count
from libearth.crawler import crawl, CrawlError
from libearth.repository import from_url
from libearth.schema import SchemaError
from libearth.session import Session
from libearth.stage import Stage
from sassutils.wsgi import SassMiddleware
from waitress import serve

from .app import app, spawn_worker

__all__ = 'crawl', 'main', 'server'


def crawl_command(args):
    repo = from_url(args.repository)
    session = Session(args.session_id)
    stage = Stage(session, repo)
    with stage:
        opml = stage.subscriptions
    if not opml:
        print('OPML does not exist in the repository', file=sys.stderr)
        return
    feed_id = args.feed_id
    if feed_id:
        feed_map = dict((sub.feed_uri, sub.feed_id)
                        for sub in opml.recursive_subscriptions
                        if sub.feed_id == feed_id)
        if not feed_map:
            print('There is no such feed:', feed_id, file=sys.stderr)
            return
    else:
        feed_map = dict((sub.feed_uri, sub.feed_id)
                        for sub in opml.recursive_subscriptions)
        if not feed_map:
            print('No feeds to crawl', file=sys.stderr)
            return
    threads_count = args.threads if args.threads is not None else cpu_count()
    iterator = iter(crawl(feed_map.keys(), threads_count))
    while 1:
        try:
            feed_url, feed_data, crawler_hints = next(iterator)
            if args.verbose:
                print('{0.title} - {1} entries'.format(
                    feed_data, len(feed_data.entries)
                ))
            with stage:
                feed_id = feed_map[feed_url]
                stage.feeds[feed_id] = feed_data
        except (CrawlError, SchemaError) as e:
            print('Something went wrong with', feed_url, file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
            else:
                print(e, file=sys.stderr)
        except StopIteration:
            break


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
    spawn_worker()
    if args.debug:
        app.wsgi_app = SassMiddleware(app.wsgi_app, {
            'earthreader.web': ('static/scss/', 'static/css/')
        })
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    else:
        serve(app, host=args.host, port=args.port)


parser = argparse.ArgumentParser(prog='earthreader')
subparsers = parser.add_subparsers(dest='command')

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
server_parser.add_argument('-i', '--session-id',
                           default=Session().identifier,
                           help='session identifier.  [default: %(default)s]')
server_parser.add_argument('-P', '--profile', '--linesman',
                           default=False,
                           action='store_true',
                           help="profile using linesman.  it's available only "
                                'when linesman is installed')
server_parser.add_argument('repository', help='repository for Earth Reader')

crawl_parser = subparsers.add_parser('crawl', help='crawl feeds in the opml')
crawl_parser.set_defaults(function=crawl_command)
crawl_parser.add_argument('-n', '--threads',
                          type=int,
                          help='the number of workers')
crawl_parser.add_argument('-i', '--session-id',
                          default=Session().identifier,
                          help='session identifier.  [default: %(default)s]')
crawl_parser.add_argument('-v', '--verbose', default=False, action='store_true',
                          help='verbose mode')
crawl_parser.add_argument('-f', '--feed-id',
                          help='crawl only the specified feed.  '
                               'crawl all subscriptions by default')
crawl_parser.add_argument('repository', help='repository which has the opml')


def main():
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        exit(1)

    url = urlparse.urlparse(args.repository)
    if url.scheme == '':
        args.repository = urlparse.urljoin(
            'file://', os.path.join(os.getcwd(), args.repository))

    args.function(args)


if __name__ == '__main__':
    main()
