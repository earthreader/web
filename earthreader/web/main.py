""":mod:`earthreader.web.main` --- Main pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Blueprint, render_template

from .stage import stage


bp = Blueprint(__name__, 'main')


@bp.route('/')
def home():
    feeds = get_feeds()
    categories = get_categories()
    return render_template('home.html', feeds=feeds, categories=categories)


@bp.route('/entries/<feed_id>/')
def entries(feed_id):
    feed = get_feed(feed_id)
    return render_template('entries.html', feed=feed, feed_id=feed_id)


@bp.route('/entry/<feed_id>/<path:entry_id>')
def entry(feed_id, entry_id):
    feed = get_feed(feed_id)
    entry = get_entry(feed, entry_id)
    return render_template('entry.html', feed=feed, feed_id=feed_id,
                           entry=entry)


@bp.route('/category/<category_id>/')
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
