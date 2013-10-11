from collections import deque
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


def feedlist_exists():
    REPOSITORY = app.config['REPOSITORY']
    OPML = app.config['OPML']
    if not os.path.isfile(REPOSITORY + OPML):
        return False
    return True


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


def get_all_feeds(category, parent_categories=[]):
    feeds = []
    categories = []
    if parent_categories:
        feed_path = '/'.join(parent_categories)
    else:
        feed_path = '/'
    for child in category:
        if isinstance(child, FeedOutline):
            feed_id = get_hash(child.xml_url)
            feeds.append({
                'title': child.title,
                'entries_url': url_for(
                    'feed_entries',
                    category_id=feed_path,
                    feed_id=feed_id,
                    _external=True
                )
            })
        elif isinstance(child, CategoryOutline):
            categories.append({
                'title': child.title,
                'category_url': url_for(
                    'feeds',
                    category_id=feed_path + '/' + child.title
                    if parent_categories else child.title,
                    _external=True
                ),
                'entries_url': url_for(
                    'category_entries',
                    category_id=feed_path + '/' + child.title
                    if parent_categories else child.title,
                    _external=True
                )
            })
    return feeds, categories


def check_path_valid(category_id, return_category_parent=False):
    if category_id == '/':
        feed_list = get_feedlist()
        return feed_list, feed_list, None
    if return_category_parent:
        category_list = category_id.split('/')
        target = category_list.pop()
        categories = deque(category_list)
    else:
        target = None
        categories = deque(category_id.split('/'))
    feed_list = get_feedlist()
    cursor = feed_list
    while categories:
        is_searched = False
        looking_for = categories.popleft()
        for category in cursor:
            if category.text == looking_for:
                is_searched = True
                cursor = category
                break
        if not is_searched:
            return None, None, None
    return feed_list, cursor, target


def find_feed_in_opml(feed_id, category, parent_categories=[], result=[]):
    categories = []
    if parent_categories:
        feed_path = '/'.join(parent_categories)
    else:
        feed_path = '/'
    for child in category:
        if isinstance(child, FeedOutline):
            current_feed_id = hashlib.sha1(binary(child.xml_url)).hexdigest()
            if current_feed_id == feed_id:
                result.append(feed_path)
        elif isinstance(child, CategoryOutline):
            categories.append(child)
    for category in categories:
        find_feed_in_opml(
            feed_id,
            category,
            parent_categories.append(category.title)
            if parent_categories else [category.title],
            result
        )
    return result


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/feeds/', defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/')
def feeds(category_id):
    feed_list, cursor, _ = check_path_valid(category_id)
    if not feed_list:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    feeds, categories = get_all_feeds(cursor, [category_id])
    return jsonify(feeds=feeds, categories=categories)


POST_FEED = 'feed'
POST_CATEGORY = 'category'


@app.route('/feeds/', methods=['POST'], defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/', methods=['POST'])
def post_feed_or_category(category_id):
    REPOSITORY = app.config['REPOSITORY']
    feed_list, cursor, _ = check_path_valid(category_id)
    if (not isinstance(cursor, CategoryOutline) and
            not isinstance(cursor, FeedList)):
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    if request.form['type'] == POST_FEED:
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
        outline = FeedOutline('atom', feed.title.value, feed_url)
        for link in feed.links:
                if link.relation == 'alternate' and \
                        link.mimetype == 'text/html':
                    outline.blog_url = link.uri
        cursor.append(outline)
        feed_list.save_file()
        file_name = hashlib.sha1(binary(feed_url)).hexdigest() + '.xml'
        with open(os.path.join(REPOSITORY, file_name), 'w') as f:
            for chunk in write(feed, indent='    ', canonical_order=True):
                f.write(chunk)
        return feeds(category_id)
    elif request.form['type'] == POST_CATEGORY:
        title = request.form['title']
        outline = CategoryOutline(title)
        cursor.append(outline)
        feed_list.save_file()
        return feeds(category_id)


@app.route('/<path:category_id>/', methods=['DELETE'])
def delete_category(category_id):
    feed_list, cursor, target = check_path_valid(category_id, True)
    if not cursor:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    for child in cursor:
        if isinstance(child, CategoryOutline):
            if child.text == target:
                cursor.remove(child)
    feed_list.save_file()
    index = category_id.rfind('/')
    if index == -1:
        return feeds('/')
    else:
        return feeds(category_id[:index])


@app.route('/feeds/<feed_id>/', methods=['DELETE'],
           defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/<feed_id>/', methods=['DELETE'])
def delete_feed(category_id, feed_id):
    REPOSITORY = app.config['REPOSITORY']
    feed_list, cursor, _ = check_path_valid(category_id)
    if not cursor:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    target = None
    for feed in cursor:
        if isinstance(feed, FeedOutline):
            if feed_id == hashlib.sha1(binary(feed.xml_url)).hexdigest():
                target = feed
    if target:
        cursor.remove(target)
    else:
        r = jsonify(
            error='feed-not-found-in-path',
            message='Given feed does not exists in the path'
        )
        r.status_code = 400
        return r
    feed_list.save_file()
    if not find_feed_in_opml(feed_id, feed_list):
        os.remove(REPOSITORY + feed_id + '.xml')
    return feeds(category_id)


@app.route('/feeds/<feed_id>/entries/', defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/<feed_id>/entries/')
def feed_entries(category_id, feed_id):
    if not check_path_valid(category_id)[0]:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
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
                        category_id=category_id,
                        feed_id=feed_id,
                        entry_id=get_hash(entry.id),
                        _external=True
                    ),
                    'updated': entry.updated_at.__str__()
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


@app.route('/<path:category_id>/entries/')
def category_entries(category_id):
    REPOSITORY = app.config['REPOSITORY']
    lst, cursor, target = check_path_valid(category_id)

    if not cursor:
        r = jsonify(
            error='category-path-invalid',
            message='Given category was not found'
        )
        r.status_code = 404
        return r

    entries = []
    for child in cursor.get_all_feeds():
        feed_id = get_hash(child.xml_url)
        with open(os.path.join(
                REPOSITORY, feed_id + '.xml'
        )) as f:
            feed = read(Feed, f)
            for entry in feed.entries:
                entries.append({
                    'title': entry.title,
                    'entry_url': url_for(
                        'feed_entry',
                        feed_id=feed_id,
                        entry_id=get_hash(entry.id),
                        _external=True
                    ),
                    'updated': entry.updated_at.__str__()
                })
    return jsonify(
        title=category_id,
        entries=entries
    )


@app.route('/feeds/<feed_id>/entries/<entry_id>/',
           defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/')
def feed_entry(category_id, feed_id, entry_id):
    if not check_path_valid(category_id)[0]:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    REPOSITORY = app.config['REPOSITORY']
    try:
        with open(os.path.join(REPOSITORY, feed_id + '.xml')) as f:
            feed = read(Feed, f)
            for entry in feed.entries:
                if entry_id == get_hash(entry.id):
                    return jsonify(
                        title=entry.title,
                        content=entry.content,
                        updated=entry.updated_at.__str__()
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
