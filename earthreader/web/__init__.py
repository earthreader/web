import glob
import hashlib
import os.path

from libearth.compat import text
from libearth.feed import Feed
from libearth.schema import read
from libearth.schema import read, write

from flask import Flask, abort, jsonify, request, url_for


app = Flask(__name__)


app.config.update(dict(
    repository='repo/'
))


@app.route('/feeds/', methods=['GET'])
def feeds():
    REPOSITORY = app.config['repository']
    feedlist = glob.glob(REPOSITORY+'*')
    feeds = []
    for xml in feedlist:
        if not xml.endswith('.xml'):
            continue
        with open(xml) as f:
            feed = read(Feed, f)
            feeds.append({
                'title': text(feed.title),
                'feed_url': url_for(
                    'entries',
                    feed_id=xml,
                    _external=True)
                })
    return jsonify(feeds=feeds)


@app.route('/feeds/<feed_id>/')
def entries(feed_id):
    REPOSITORY = app.config['repository']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            entries = []
            for entry in feed.entries:
                entries.append({
                    'title': text(entry.title),
                    'entry_url': url_for(
                        'entry',
                        feed_id=feed_id,
                        entry_id=hashlib.sha1(entry.id).hexdigest(),
                        _external=True
                    )
                })
        return jsonify(entries=entries)
    except IOError:
        abort(404)


@app.route('/feeds/<feed_id>/<entry_id>/')
def entry(feed_id, entry_id):
    pass
