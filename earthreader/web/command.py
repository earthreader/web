import argparse
import hashlib
import os.path
import socket

from earthreader.web import app

from libearth.crawler import crawl, CrawlError
from libearth.repository import FileSystemRepository
from libearth.session import Session
from libearth.stage import Stage


def earthreader():
    parser = argparse.ArgumentParser(prog='earthreader')
    subparsers = parser.add_subparsers(dest='command', help='command-help')
    server_parser = subparsers.add_parser('server',
                                          help='Run a server for EarthReader')
    server_parser.add_argument('-H', '--host',
                               default='0.0.0.0',
                               help='Host to listen. default=\'0.0.0.0\'')
    server_parser.add_argument('-p', '--port',
                               type=int,
                               default=5000,
                               help='Port number to listen. default=5000')
    server_parser.add_argument('-d', '--debug',
                               default=False,
                               action='store_true',
                               help='Debug mode. '
                                    'It makes the server possible to '
                                    'automatically restart when files touched.')
    server_parser.add_argument('repository',
                               help='Repository for EarthReader')
    crawl_parser = subparsers.add_parser('crawl',
                                         help='Crawl feeds in the OPML')
    crawl_parser.add_argument('-n', '--threads',
                              type=int,
                              help='Poolsize of the crawler')
    crawl_parser.add_argument('repository',
                              help='Repository which has the OPML')
    args = parser.parse_args()

    if args.command == 'server':
        repository = args.repository
        if not os.path.isdir(repository):
            os.mkdir(repository)
        app.config.update(dict(
            REPOSITORY=repository
            ))
        try:
            app.run(host=args.host, port=args.port, debug=args.debug)
        except socket.error as e:
            parser.error(str(e))

    elif args.command == 'crawl':
        repo = FileSystemRepository(args.repository)
        session = Session()
        stage = Stage(session, repo)
        opml = stage.subscriptions
        if not opml:
            print('OPML does not exist in the repository')
            return
        urllist = [subscription.feed_uri for subscription
                   in opml.recursive_subscriptions]
        generator = crawl(urllist, args.threads)
        try:
            for feed_url, (feed_data, crawler_hints) in generator:
                feed_id = hashlib.sha1(feed_url).hexdigest()
                stage.feeds[feed_id] = feed_data
        except CrawlError as e:
            print(e.msg)
