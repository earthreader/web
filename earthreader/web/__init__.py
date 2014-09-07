""":mod:`earthreader.web` --- Earth Reader for Web
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Flask, render_template

from .stage import stage
from .wsgi import MethodRewriteMiddleware


app = Flask(__name__)
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)


@app.route('/')
def home():
    feeds = get_feeds()
    categories = get_categories()
    return render_template('home.html', feeds=feeds, categories=categories)


@app.route('/entries/<feed_id>/')
def entries(feed_id):
    feed = get_feed(feed_id)
    return render_template('entries.html', feed=feed, feed_id=feed_id)


@app.route('/entry/<feed_id>/<path:entry_id>')
def entry(feed_id, entry_id):
    feed = get_feed(feed_id)
    entry = get_entry(feed, entry_id)
    return render_template('entry.html', feed=feed, feed_id=feed_id,
                           entry=entry)


@app.route('/category/<category_id>/')
def category(category_id):
    category = get_category(category_id)
    return render_template('category.html', category=category)


def get_entry(feed, entry_id):
    with stage:
        for entry in feed.entries:
            if entry.id == entry_id:
                return entry


def get_feed(feed_id):
    with stage:
        return stage.feeds[feed_id]


def get_feeds():
    with stage:
        return {feed_id: stage.feeds[feed_id] for feed_id in stage.feeds}


def get_category(category_id):
    with stage:
        return stage.subscriptions.categories[category_id]


def get_categories():
    with stage:
        return stage.subscriptions.categories
