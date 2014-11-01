""":mod:`earthreader.web.main` --- Main pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Blueprint, render_template, jsonify

from .stage import stage
from .util import request_wants_json


bp = Blueprint(__name__, 'main')


@bp.route('/')
def home():
    with stage:
        subscriptions = stage.subscriptions
    return render_template('home.html', subscriptions=subscriptions)


@bp.route('/feeds/')
def feeds():
    with stage:
        feeds = stage.subscriptions.recursive_subscriptions
    if request_wants_json():
        feeds = [{'id': feed.feed_id, 'label': feed.label} for feed in feeds]
        return jsonify(feeds=feeds)
    return render_template('feeds.html', feeds=feeds)


@bp.route('/<feed_id>/')
def entries(feed_id):
    with stage:
        feed = stage.feeds[feed_id]
    if request_wants_json():
        entries = [{'id': entry.id, 'title': entry.title}
                   for entry in feed.entries]
        return jsonify(entries=entries)
    return render_template('entries.html', feed=feed, feed_id=feed_id)


@bp.route('/<feed_id>/<path:entry_id>')
def entry(feed_id, entry_id):
    with stage:
        feed = stage.feeds[feed_id]
    entry = get_entry(feed, entry_id)
    if not entry.read:
        entry.read = True
        with stage:
            stage.feeds[feed_id] = feed
    return render_template('entry.html', feed=feed, feed_id=feed_id,
                           entry=entry)


@bp.route('/category/<category_label>/')
def category(category_label):
    with stage:
        category = stage.subscriptions.categories[category_label]
    return render_template('category.html', category=category)


def get_entry(feed, entry_id):
    with stage:
        for entry in feed.entries:
            if entry.id == entry_id:
                return entry
    return None
