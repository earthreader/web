import glob
import hashlib
import os.path
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from libearth.compat import binary
from libearth.feed import Feed
from libearth.feedlist import (Feed as FeedOutline,
                               FeedCategory as CategoryOutline, FeedList)
from libearth.parser.autodiscovery import autodiscovery, FeedUrlNotFoundError
from libearth.parser.heuristic import get_format
from libearth.schema import read, write

from flask import Flask, jsonify, render_template, request, url_for


app = Flask(__name__)


app.config.update(dict(
    REPOSITORY='repo/',
    OPML='earthreader.opml'
))


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def get_all_feeds(category, parent_categories=[]):
    result = []
    categories = []
    if parent_categories:
        feed_path = '/'.join(parent_categories)
        feed_path = '/' + feed_path + '/'
    else:
        feed_path = '/'
    for child in category:
        if isinstance(child, FeedOutline):
            feed_id = hashlib.sha1(child.xml_url).hexdigest()
            feed_url = feed_path + feed_id + '/entries/'
            result.append({
                'title': child.title,
                'feed_url': feed_url
            })
        elif isinstance(child, CategoryOutline):
            categories.append(child)
    for category in categories:
        result.append({
            'title': category.title,
            'feed_url': feed_path + category.title + '/entries',
            'feeds': get_all_feeds(category,
                parent_categories.append(category.title)
                if parent_categories else [category.title]
            )
        })
    return result


@app.route('/feeds/', methods=['GET'])
def feeds():
    REPOSITORY = app.config['REPOSITORY']
    OPML = app.config['OPML']
    if not os.path.isfile(REPOSITORY + OPML):
        r = jsonify(
            error='opml-not-found',
            message='Cannot open OPML'
        )
        r.status_code = 400
        return r
    feed_list = FeedList(REPOSITORY + OPML)
    feeds = get_all_feeds(feed_list, None)
    return jsonify(feeds=feeds)
