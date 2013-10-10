import glob
import hashlib
import os.path
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from libearth.compat import binary
from libearth.feed import Feed
from libearth.feedlist import Feed as OutLine, FeedList
from libearth.parser.autodiscovery import autodiscovery, FeedUrlNotFoundError
from libearth.parser.heuristic import get_format
from libearth.schema import read, write

from flask import Flask, jsonify, render_template, request, url_for


app = Flask(__name__)


app.config.update(dict(
    REPOSITORY='repo/',
    OPML='earthreader.opml'
))


def get_feedlist():
    REPOSITORY = app.config['REPOSITORY']
    OPML = app.config['OPML']
    if not os.path.isfile(REPOSITORY + OPML):
        if not os.path.isdir(REPOSITORY):
            os.mkdir(REPOSITORY)
        feed_list = FeedList()
        feed_list.save_file(REPOSITORY + OPML)

    feed_list = FeedList(REPOSITORY + OPML)

    return feed_list


def get_hash(name):
    return hashlib.sha1(binary(name)).hexdigest()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/feeds/', methods=['GET'])
def feeds():
    feedlist = get_feedlist()

    def makeCategory(category):
        feeds = []
        for obj in category:
            if isinstance(obj, OutLine):
                feeds.append({
                    'title': obj.title,
                    'feed_url': url_for(
                        'entries',
                        feed_id=get_hash(obj.xml_url),
                        _external=True)
                })
            else:
                feeds.append({
                    'title': obj.title,
                    'feed_url': url_for(
                        'entries',
                        feed_id=get_hash(obj.title),
                        _external=True),
                    'feeds': makeCategory(obj)
                })

        return feeds

    feeds = makeCategory(feedlist)

    return jsonify(feeds=feeds)


@app.route('/feeds/', methods=['POST'])
def add_feed():
    REPOSITORY = app.config['REPOSITORY']

    feed_list = get_feedlist()
    try:
        url = request.form['url']
        f = urllib2.urlopen(url)
        document = f.read()
    except ValueError:
        r = jsonify(
            error='unreachable-url',
            message='Cannot connect to given url'
        )
        r.status_code = 400
        return r
    try:
        feed_url = autodiscovery(document, url)
    except FeedUrlNotFoundError:
        r = jsonify(
            error='unreachable-feed-url',
            message='Cannot find feed url'
        )
        r.status_code = 400
        return r
    if not feed_url == url:
        f.close()
        f = urllib2.urlopen(feed_url)
        xml = f.read()
    else:
        xml = document
    format = get_format(xml)
    result = format(xml, feed_url)
    feed = result[0]
    for link in feed.links:
            if link.relation == 'alternate' and link.mimetype == 'text/html':
                blog_url = link.uri
    outline = OutLine('atom', feed.title.value, feed_url, blog_url)
    feed_list.append(outline)
    feed_list.save_file()
    file_name = get_hash(feed_url) + '.xml'
    with open(os.path.join(REPOSITORY, file_name), 'w') as f:
        for chunk in write(feed, indent='    ', canonical_order=True):
            f.write(chunk)
    return feeds()


@app.route('/feeds/<feed_id>/', methods=['DELETE'])
def delete_feed(feed_id):
    REPOSITORY = app.config['REPOSITORY']
    feed_list = get_feedlist()
    for feed in feed_list:
        if feed_id == get_hash(feed.xml_url):
            feed_list.remove(feed)
    feed_list.save_file()
    xml_list = glob.glob(REPOSITORY + '*')
    for xml in xml_list:
        if xml == REPOSITORY + feed_id + '.xml':
            os.remove(xml)
    return feeds()


@app.route('/feeds/<feed_id>/')
def entries(feed_id):
    REPOSITORY = app.config['REPOSITORY']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            entries = []
            for entry in feed.entries:
                entries.append({
                    'title': entry.title,
                    'entry_url': url_for(
                        'entry',
                        feed_id=feed_id,
                        entry_id=get_hash(entry.id),
                        _external=True
                    )
                })
        return jsonify(
            title=feed.title,
            entries=entries
        )
    except IOError:
        r = jsonify(
            error='feed-not-found',
            message='Given feed does not exist'
        )
        r.status_code = 404
        return r


@app.route('/feeds/<feed_id>/<entry_id>/')
def entry(feed_id, entry_id):
    REPOSITORY = app.config['REPOSITORY']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            for entry in feed.entries:
                if entry_id == get_hash(entry.id):
                    return jsonify(
                        content=entry.content
                    )
            r = jsonify(
                error='entry-not-found',
                message='Given entry does not exist'
            )
            r.status_code = 404
            return r

    except IOError:
        r = jsonify(
            error='feed-not-found',
            message='Given feed does not exist'
        )
        r.status_code = 404
        return r
