import collections
import datetime
import hashlib
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from flask import Flask, jsonify, render_template, request, url_for
from libearth.codecs import Rfc3339
from libearth.compat import binary
from libearth.parser.autodiscovery import autodiscovery, FeedUrlNotFoundError
from libearth.parser.heuristic import get_format
from libearth.repository import FileSystemRepository
from libearth.session import Session
from libearth.stage import Stage
from libearth.subscribe import Category, Subscription, SubscriptionList
from libearth.tz import now

from .wsgi import MethodRewriteMiddleware


app = Flask(__name__)
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)


app.config.update(dict(
    ALLFEED='All Feeds',
))


def get_stage():
    session = Session()
    repo = FileSystemRepository(app.config['REPOSITORY'])
    return Stage(session, repo)


def feedlist_exists():
    stage = get_stage()
    if stage.subscriptions:
        return True
    else:
        return False


iterators = {}


def tidy_iterators_up():
    global iterators
    lists = []
    for key, (it, time_saved) in iterators.items():
        if time_saved >= now() - datetime.timedelta(minutes=30):
            lists.append((key, (it, time_saved)))
        if len(lists) >= 10:
            break
    iterators = dict(lists)


def get_feeds(cursor):
    feeds = []
    for child in cursor:
        if isinstance(child, Subscription):
            feeds.append(get_hash(child.feed_uri))
        elif isinstance(child, Category):
            feeds.extend(get_feeds(child))
    return feeds


def get_entries(feed_list, category_id):
    tidy_iterators_up()
    stage = get_stage()
    url_token = request.args.get('url_token')
    feed_title = None
    it = None
    if url_token:
        pair = iterators.get(url_token)
        if pair:
            it = pair[0]
    if not it:
        feed_permalinks = {}
        sorting_pool = []
        for feed_id in feed_list:
            feed = stage.feeds[feed_id]
            feed_permalink = feed_permalinks.get(feed_id)
            if not feed_permalink:
                for link in feed.links:
                    if link.relation == 'alternate' and \
                            link.mimetype == 'text/html':
                        feed_permalinks[feed_id] = link.uri
                        feed_permalink = link.uri
                if not feed_permalink:
                    feed_permalinks[feed_id] = feed.id
                    feed_permalink = feed.id
            for entry in feed.entries:
                sorting_pool.append((feed.title, feed_id,
                                    feed_permalink, entry))
        sorting_pool.sort(key=lambda entry: entry[3].updated_at,
                          reverse=True)
        it = iter(sorting_pool)
        if not url_token:
            url_token = now().__str__()
        iterators[url_token] = it, now()
    entry_after = None
    entry_after = request.args.get('entry_after')
    next_key = None
    if entry_after:
        next_key = Rfc3339().decode(entry_after.replace(' ', 'T'))
    entries = []
    while len(entries) < 20:
        try:
            feed_title, feed_id, feed_permalink, entry = next(it)
        except StopIteration:
            iterators.pop(url_token)
            break
        if next_key and entry.updated_at >= next_key:
            continue
        entry_permalink = None
        for link in entry.links:
            if link.relation == 'alternate' and \
                    link.mimetype == 'text/html':
                entry_permalink = link.uri
        if not entry_permalink:
            entry_permalink = entry.id
        entries.append({
            'title': entry.title,
            'entry_url': url_for(
                'feed_entry',
                category_id=category_id,
                feed_id=feed_id,
                entry_id=get_hash(entry.id),
                _external=True
            ),
            'permalink': entry_permalink or None,
            'updated': entry.updated_at.__str__(),
            'feed': {
                'title': feed_title,
                'entries_url': url_for(
                    'feed_entries',
                    feed_id=feed_id
                ),
                'permalink': feed_permalink or None
            }
        })
    tidy_iterators_up()
    return feed_title if len(feed_list) == 1 else None, entries, url_token


def get_hash(name):
    return hashlib.sha1(binary(name)).hexdigest()


def get_all_feeds(category, path=None):
    feeds = []
    categories = []
    if not path:
        feed_path = '/'
    else:
        feed_path = path
    for child in category:
        if isinstance(child, Subscription):
            feed_id = get_hash(child.feed_uri)
            feeds.append({
                'title': child._title,
                'entries_url': url_for(
                    'feed_entries',
                    category_id=feed_path,
                    feed_id=feed_id,
                    _external=True
                ),
                'remove_feed_url': url_for(
                    'delete_feed',
                    category_id=feed_path,
                    feed_id=feed_id,
                    _external=True
                )
            })
        elif isinstance(child, Category):
            categories.append({
                'title': child._title,
                'feeds_url': url_for(
                    'feeds',
                    category_id=feed_path + '/-' + child._title
                    if path else '-' + child._title,
                    _external=True
                ),
                'entries_url': url_for(
                    'category_entries',
                    category_id=feed_path + '/-' + child._title
                    if path else '-' + child._title,
                    _external=True
                ),
                'add_feed_url': url_for(
                    'add_feed',
                    category_id=feed_path + '/-' + child._title
                    if path else '-' + child._title,
                    _external=True
                ),
                'add_category_url': url_for(
                    'add_category',
                    category_id=feed_path + '/-' + child._title
                    if path else '-' + child._title,
                    _external=True
                ),
                'remove_category_url': url_for(
                    'delete_category',
                    category_id=feed_path + '/-' + child._title
                    if path else '-' + child._title,
                    _external=True
                ),
            })
    return feeds, categories


def check_path_valid(category_id, return_category_parent=False):
    stage = get_stage()
    if not stage.subscriptions:
        subscriptions = SubscriptionList()
        stage.subscriptions = subscriptions
    if category_id == '/':
        subscriptions = stage.subscriptions
        return subscriptions, subscriptions, None
    if return_category_parent:
        category_list = category_id.split('/')
        target = category_list.pop()[1:]
        categories = collections.deque([category[1:] for category
                                       in category_list])
    else:
        target = None
        categories = collections.deque([category[1:] for category in
                                       category_id.split('/')])
    feed_list = stage.subscriptions
    cursor = feed_list
    while categories:
        looking_for = categories.popleft()
        try:
            cursor = cursor.categories[looking_for]
        except KeyError:
            return None, None, None
    return feed_list, cursor, target


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/feeds/', defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/')
def feeds(category_id):
    feed_list, cursor, _ = check_path_valid(category_id)
    if not isinstance(feed_list, SubscriptionList):
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    feeds, categories = get_all_feeds(cursor, category_id)
    return jsonify(feeds=feeds, categories=categories)


@app.route('/feeds/', methods=['POST'], defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/', methods=['POST'])
def add_feed(category_id):
    stage = get_stage()
    subscriptions, cursor, _ = check_path_valid(category_id)
    if (not isinstance(cursor, Category) and
            not isinstance(cursor, SubscriptionList)):
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
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
        feed_links = autodiscovery(document, url)
    except FeedUrlNotFoundError:
        r = jsonify(
            error='unreachable-feed-url',
            message='Cannot find feed url'
        )
        r.status_code = 400
        return r
    feed_url = feed_links[0].url
    if not feed_url == url:
        f.close()
        f = urllib2.urlopen(feed_url)
        xml = f.read()
    else:
        xml = document
    format = get_format(xml)
    result = format(xml, feed_url)
    feed = result[0]
    subscription = Subscription(type='atom', label=feed.title.value,
                                _title=feed.title.value,
                                feed_uri=feed_url)
    for link in feed.links:
            if link.relation == 'alternate' and \
                    link.mimetype == 'text/html':
                subscription.alternate_uri = link.uri
    cursor.add(subscription)
    stage.subscriptions = subscriptions
    feed_id = get_hash(feed_url) + '.xml'
    stage.feeds[feed_id] = feed
    return feeds(category_id)


@app.route('/', methods=['POST'], defaults={'category_id': '/'})
@app.route('/<path:category_id>/', methods=['POST'])
def add_category(category_id):
    stage = get_stage()
    subscriptions, cursor, _ = check_path_valid(category_id)
    if (not isinstance(cursor, Category) and
            not isinstance(cursor, SubscriptionList)):
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r

    title = request.form['title']
    outline = Category(label=title, _title=title)
    cursor.add(outline)
    stage.subscriptions = subscriptions
    return feeds(category_id)


@app.route('/<path:category_id>/', methods=['DELETE'])
def delete_category(category_id):
    stage = get_stage()
    subscriptions, cursor, target = check_path_valid(category_id, True)
    if not cursor:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    for child in cursor:
        if isinstance(child, Category):
            if child.label == target:
                cursor.remove(child)
    stage.subscriptions = subscriptions
    index = category_id.rfind('/')
    if index == -1:
        return feeds('/')
    else:
        return feeds(category_id[:index])


@app.route('/feeds/<feed_id>/', methods=['DELETE'],
           defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/<feed_id>/', methods=['DELETE'])
def delete_feed(category_id, feed_id):
    stage = get_stage()
    subscriptions, cursor, _ = check_path_valid(category_id)
    if not cursor:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    target = None
    for subscription in cursor:
        if isinstance(subscription, Subscription):
            if feed_id == hashlib.sha1(
                    binary(subscription.feed_uri)).hexdigest():
                target = subscription
    if target:
        cursor.discard(target)
    else:
        r = jsonify(
            error='feed-not-found-in-path',
            message='Given feed does not exists in the path'
        )
        r.status_code = 400
        return r
    stage.subscriptions = subscriptions
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
    feed_title, entries, url_token = get_entries([feed_id], category_id)
    if len(entries) < 20:
        next_url = None
    else:
        next_url = url_for(
            'feed_entries',
            category_id=category_id,
            feed_id=feed_id,
            url_token=url_token,
            entry_after=entries[-1]['updated'] if entries else None
        )
    return jsonify(
        title=feed_title,
        entries=entries,
        next_url=next_url
    )


@app.route('/entries/', defaults={'category_id': '/'})
@app.route('/<path:category_id>/entries/')
def category_entries(category_id):
    subscriptions, cursor, target = check_path_valid(category_id)
    if not isinstance(subscriptions, SubscriptionList):
        r = jsonify(
            error='category-path-invalid',
            message='Given category was not found'
        )
        r.status_code = 404
        return r
    feed_list = get_feeds(cursor)
    _, entries, url_token = get_entries(feed_list, category_id)
    if len(entries) < 20:
        next_url = None
    else:
        next_url = url_for(
            'category_entries',
            category_id=category_id,
            url_token=url_token,
            entry_after=entries[-1]['updated'] if entries else None
        )
    return jsonify(
        title=category_id.split('/')[-1][1:] or app.config['ALLFEED'],
        entries=entries,
        next_url=next_url
    )


@app.route('/feeds/<feed_id>/entries/<entry_id>/',
           defaults={'category_id': '/'})
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/')
def feed_entry(category_id, feed_id, entry_id):
    stage = get_stage()
    if not check_path_valid(category_id)[0]:
        r = jsonify(
            error='category-path-invalid',
            message='Given category path is not valid'
        )
        r.status_code = 404
        return r
    try:
        feed = stage.feeds[feed_id]
    except KeyError:
        r = jsonify(
            error='feed-not-found',
            message='Given feed does not exist'
        )
        r.status_code = 404
        return r
    feed_permalink = None
    for link in feed.links:
        if link.relation == 'alternate'\
           and link.mimetype == 'text/html':
            feed_permalink = link.uri
        if not feed_permalink:
            feed_permalink = feed.id
    for entry in feed.entries:
        entry_permalink = None
        for link in entry.links:
            if link.relation == 'alternate'\
               and link.mimetype == 'text/html':
                entry_permalink = link.uri
        if not entry_permalink:
            entry_permalink = entry.id
        if entry_id == get_hash(entry.id):
            return jsonify(
                title=entry.title,
                content=entry.content.sanitized_html
                if entry.content else entry.summary.sanitized_html,
                updated=entry.updated_at.__str__(),
                permalink=entry_permalink or None,
                feed={
                    'title': feed.title,
                    'entries_url': url_for(
                        'feed_entries',
                        feed_id=feed_id,
                        _external=True
                    ),
                    'permalink': feed_permalink or None
                }
            )
    r = jsonify(
        error='entry-not-found',
        message='Given entry does not exist'
    )
    r.status_code = 404
    return r
