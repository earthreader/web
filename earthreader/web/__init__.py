import glob
import hashlib
import os.path
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from libearth.compat import binary, binary_type
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
    else:
        feed_path = '/'
    for child in category:
        if isinstance(child, FeedOutline):
            feed_id = hashlib.sha1(child.xml_url).hexdigest()
            result.append({
                'title': child.title,
                'feed_url': url_for(
                    'category_feed_entries',
                    category_id = feed_path,
                    feed_id = feed_id
                )
            })
        elif isinstance(child, CategoryOutline):
            categories.append(child)
    for category in categories:
        result.append({
            'title': category.title,
            'feed_url': feed_path + category.title + '/feeds/',
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


@app.route('/feeds/<feed_id>/entries/')
def feed_entries(feed_id):
    REPOSITORY = app.config['REPOSITORY']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            entries = []
            for entry in feed.entries:
                entries.append({
                    'title': entry.title,
                    'entry_url': url_for(
                        'feed_entry',
                        feed_id=feed_id,
                        entry_id=hashlib.sha1(binary(entry.id)).hexdigest(),
                        _external=True
                    ),
                    'updated': entry.published_at
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


@app.route('/<path:category_id>/feeds/<feed_id>/entries/')
def category_feed_entries(category_id, feed_id):
    return feed_entries(feed_id)


@app.route('/feeds/<feed_id>/entries/<entry_id>/')
def feed_entry(feed_id, entry_id):
    REPOSITORY = app.config['REPOSITORY']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            for entry in feed.entries:
                if entry_id == hashlib.sha1(binary(entry.id)).hexdigest():
                    return jsonify(
                        content=entry.content,
                        updated=binary_type(entry.updated_at)
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


@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/')
def category_feed_entry(category_id, feed_id, entry_id):
    return feed_entry(feed_id, entry_id)
