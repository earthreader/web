import hashlib
import os.path

from libearth.compat import text
from libearth.feed import Feed
from libearth.schema import read

from flask import Flask, abort, jsonify, request, url_for


app = Flask(__name__)


@app.route('/feeds/', methods=['GET', 'POST', 'DELETE'])
def feeds():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass
    elif request.method == 'DELETE':
        pass


@app.route('/feeds/<feed_id>/')
def entries(feed_id):
    try:
        with open(os.path.join('repo', feed_id + '.xml')) as f:
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
