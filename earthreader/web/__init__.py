""":mod:`earthreader.web` --- Earth Reader for Web
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import os

from flask import Flask, g, jsonify, render_template, request, url_for
from libearth.codecs import Rfc3339
from libearth.compat import text_type
from libearth.crawler import crawl, open_url
from libearth.parser.autodiscovery import autodiscovery, FeedUrlNotFoundError
from libearth.subscribe import Category, Subscription, SubscriptionList
from libearth.tz import now, utc
from werkzeug.local import LocalProxy

from .util import autofix_repo_url, get_hash
from .wsgi import MethodRewriteMiddleware
from .exceptions import (AutodiscoveryFailed, CategoryCircularReference,
                         DocumentNotFound, InvalidCategoryID, IteratorNotFound,
                         WorkerNotRunning, FeedNotFound, FeedNotFoundInCategory,
                         EntryNotFound)
from .worker import Worker
from .transaction import SubscriptionTransaction


app = Flask(__name__)
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

app.config.update(
    ALLFEED='All Feeds',
    SESSION_ID=None,
    PAGE_SIZE=20,
    CRAWLER_THREAD=4,
    USE_WORKER=True,
    )


# Load EARTHREADER_REPOSITORY environment variable if present.
try:
    app.config['REPOSITORY'] = os.environ['EARTHREADER_REPOSITORY']
except KeyError:
    pass
worker = Worker(app)


@app.before_first_request
def initialize():
    if 'REPOSITORY' in app.config:
        app.config['REPOSITORY'] = autofix_repo_url(app.config['REPOSITORY'])

    if app.config['USE_WORKER']:
        worker.start_worker()


@app.before_request
def before_request():
    if request.path == '/' and request.method == 'GET':
        return
    g.transaction = SubscriptionTransaction()


transaction = LocalProxy(lambda: g.transaction)


def join_category_id(base, append):
    if base:
        return base + '/-' + append
    return '-' + append


def add_urls(data, keys, category_id, feed_id=None, entry_id=None):
    APIS = {
        'entries_url': 'category_entries',
        'feeds_url': 'list_in_category',
        'add_feed_url': 'add_feed',
        'add_category_url': 'add_category',
        'remove_category_url': 'delete_category',
        'move_url': 'move_outline',
    }
    if feed_id is not None:
        APIS.update(
            entries_url='feed_entries',  # overwrite
            remove_feed_url='delete_feed',
        )
        if entry_id is not None:
            APIS.update(
                entry_url='feed_entry',
                read_url='read_entry',
                unread_url='unread_entry',
                star_url='star_entry',
                unstar_url='unstar_entry',
            )
    urls = {}
    for key in keys:
        if key in APIS:
            urls[key] = url_for(
                APIS[key],
                category_id=category_id,
                feed_id=feed_id,
                entry_id=entry_id,
                _external=True
            )
    data.update(urls)


def add_path_data(data, category_id, feed_id=''):
    path = ''
    if category_id:
        path = category_id
    if feed_id:
        path = path + '/feeds/' + feed_id
    data.update({'path': path})


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/feeds/', defaults={'category_id': ''})
@app.route('/<path:category_id>/feeds/')
def list_in_category(category_id):
    category = transaction.get_category(category_id)
    feeds = []
    categories = []
    for child in category:
        if isinstance(child, Subscription):
            feeds.append(get_feed_data(category_id, child))
        elif isinstance(child, Category):
            categories.append(get_category_data(category_id, child))
    return jsonify(feeds=feeds, categories=categories)


def get_feed_data(base_category_id, subscription):
    feed_data = {'title': subscription.label}
    url_keys = ['entries_url', 'remove_feed_url']
    add_urls(feed_data, url_keys, base_category_id, subscription.feed_id)
    add_path_data(feed_data, base_category_id, subscription.feed_id)
    return feed_data


def get_category_data(base_category_id, category):
    label = category.label
    category_data = {'title': label}
    url_keys = ['feeds_url', 'entries_url', 'add_feed_url',
                'add_category_url', 'remove_category_url', 'move_url']
    add_urls(category_data, url_keys, join_category_id(base_category_id, label))
    add_path_data(category_data, join_category_id(base_category_id, label))
    return category_data


@app.route('/feeds/', methods=['POST'], defaults={'category_id': ''})
@app.route('/<path:category_id>/feeds/', methods=['POST'])
def add_feed(category_id):
    category = transaction.get_category(category_id)
    url = request.form['url']
    document = get_document(url)
    feed_links = get_feed_links(document, url)
    feed_url = feed_links[0].url
    feed_url, feed, hints = next(iter(crawl([feed_url], 1)))
    transaction.add_feed(category, feed)
    transaction.save()
    return list_in_category(category_id)


def get_document(url):
    try:
        f = open_url(url)
        document = f.read()
        f.close()
        return document
    except Exception:
        raise DocumentNotFound


def get_feed_links(document, url):
    try:
        return autodiscovery(document, url)
    except FeedUrlNotFoundError:
        raise FeedUrlNotFoundError


@app.route('/', methods=['POST'], defaults={'category_id': ''})
@app.route('/<path:category_id>/', methods=['POST'])
def add_category(category_id):
    category = transaction.get_category(category_id)
    title = request.form['title']
    outline = Category(label=title)
    category.add(outline)
    transaction.save()
    return list_in_category(category_id)


@app.route('/<path:category_id>/', methods=['DELETE'])
def delete_category(category_id):
    parent_category = transaction.get_parent_category(category_id)
    target_category = transaction.get_category(category_id)
    parent_category.remove(target_category)
    transaction.save()
    index = category_id.rfind('/')
    if index == -1:
        return list_in_category('')
    else:
        return list_in_category(category_id[:index])


@app.route('/feeds/<feed_id>/', methods=['DELETE'],
           defaults={'category_id': ''})
@app.route('/<path:category_id>/feeds/<feed_id>/', methods=['DELETE'])
def delete_feed(category_id, feed_id):
    category = transaction.get_category(category_id)
    target = None
    for subscription in category:
        if isinstance(subscription, Subscription):
            if feed_id == subscription.feed_id:
                target = subscription
    if target:
        category.discard(target)
    else:
        raise FeedNotFoundInCategory
    transaction.save()
    return list_in_category(category_id)


@app.route('/<path:category_id>/feeds/', methods=['PUT'])
@app.route('/feeds/', methods=['PUT'], defaults={'category_id': ''})
def move_outline(category_id):
    source_path = request.args.get('from')
    if '/feeds/' in source_path:
        parent_category_id, feed_id = source_path.split('/feeds/')
        source = transaction.get_category(parent_category_id)
        target = None
        for child in source:
            if child.feed_id == feed_id:
                target = child
    else:
        source = transaction.get_parent_category(source_path)
        target = transaction.get_category(source_path)

    dest = transaction.get_category(category_id)
    if isinstance(target, Category) and target.contains(dest):
        raise CategoryCircularReference
    source.discard(target)
    transaction.save()
    dest = transaction.get_category(category_id)
    dest.add(target)
    transaction.save()
    return jsonify()


entry_generators = {}


def tidy_generators_up():
    global entry_generators
    generators = []
    for key, (it, time_saved) in entry_generators.items():
        if time_saved >= now() - datetime.timedelta(minutes=30):
            generators.append((key, (it, time_saved)))
    generators = sorted(generators, key=lambda generator: generator[1][1],
                        reverse=True)
    entry_generators = dict(generators[:10])


def to_bool(str_):
    return str_.strip().lower() == 'true'


def get_optional_args():
    url_token = request.args.get('url_token')
    entry_after = request.args.get('entry_after')
    read = request.args.get('read')
    starred = request.args.get('starred')
    return url_token, entry_after, read, starred


def save_entry_generators(url_token, generator):
    entry_generators[url_token] = generator, now()


def get_entry_generator(url_token):
    pair = entry_generators.get(url_token)
    if pair:
        it = pair[0]
        return it
    else:
        raise IteratorNotFound('The iterator does not exist')


def remove_entry_generator(url_token):
    if url_token in entry_generators:
        entry_generators.pop(url_token)


def get_permalink(data):
    link = data.links.permalink
    return link and link.uri or data.id


def make_next_url(category_id, url_token, entry_after, read, starred,
                  feed_id=None):
    return url_for(
        'feed_entries' if feed_id else 'category_entries',
        category_id=category_id,
        feed_id=feed_id,
        url_token=url_token,
        entry_after=entry_after,
        read=read,
        starred=starred
    )


class FeedEntryGenerator():

    def __init__(self, category_id, feed_id, feed_title, feed_permalink, it,
                 time_used, read, starred):
        self.category_id = category_id
        self.feed_id = feed_id
        self.feed_title = feed_title
        self.feed_permalink = feed_permalink
        self.it = it
        self.time_used = time_used

        self.filters = 'read', 'starred'
        self.read = read
        self.starred = starred

        self.entry = None
        self.find_next_entry()

    def next(self):
        return next(self.it)

    def __next__(self):
        return next(self.it)

    def set_iterator(self, entry_after=None):
        if entry_after:
            self.skip_to_next_entry(entry_after)
        self.skip_until_filter_matched()

    def skip_to_next_entry(self, latest_entry_id):
        while latest_entry_id and get_hash(self.entry.id) != latest_entry_id:
            self.entry = next(self.it)
        self.entry = next(self.it)

    def skip_until_filter_matched(self):
        while self.filter_not_matched():
            self.entry = next(self.it)

    def filter_not_matched(self):
        for filter in self.filters:
            arg = getattr(self, filter)
            if arg and to_bool(arg) != bool(getattr(self.entry, filter)):
                return True
        return False

    def find_next_entry(self):
        self.entry = next(self.it)
        while self.filter_not_matched():
            self.entry = next(self.it)

    def get_entry_data(self):
        if not self.entry:
            raise StopIteration
        entry_permalink = get_permalink(self.entry)
        entry_data = {
            'title': text_type(self.entry.title),
            'entry_id': get_hash(self.entry.id),
            'permalink': entry_permalink or None,
            'updated': Rfc3339().encode(self.entry.updated_at.astimezone(utc)),
            'read': bool(self.entry.read),
            'starred': bool(self.entry.starred)
        }
        feed_data = {
            'title': self.feed_title,
            'permalink': self.feed_permalink or None
        }
        add_urls(entry_data, ['entry_url'], self.category_id, self.feed_id,
                 get_hash(self.entry.id))
        add_urls(feed_data, ['entries_url'], self.category_id, self.feed_id)
        entry_data['feed'] = feed_data
        return entry_data

    def get_entries(self):
        entries = []
        while len(entries) < app.config['PAGE_SIZE']:
            try:
                entry = self.get_entry_data()
                entries.append(entry)
                self.find_next_entry()
            except StopIteration:
                self.entry = None
                return entries
        return entries


@app.route('/feeds/<feed_id>/entries/', defaults={'category_id': ''})
@app.route('/<path:category_id>/feeds/<feed_id>/entries/')
def feed_entries(category_id, feed_id):
    feed = transaction.get_feed(feed_id, category_id)
    if feed.__revision__:
        updated_at = feed.__revision__.updated_at
        if request.if_modified_since:
            if_modified_since = request.if_modified_since.replace(tzinfo=utc)
            last_modified = updated_at.replace(microsecond=0)
            if if_modified_since >= last_modified:
                return '', 304, {}  # Not Modified
    else:
        updated_at = None

    if worker.is_running():
        crawl_url = url_for('update_entries',
                            category_id=category_id,
                            feed_id=feed_id)
    else:
        crawl_url = None

    url_token, entry_after, read, starred = get_optional_args()
    generator = None
    if url_token:
        try:
            generator = get_entry_generator(url_token)
        except IteratorNotFound:
            pass
    else:
        url_token = text_type(now())
    if not generator:
        it = iter(feed.entries)
        feed_title = text_type(feed.title)
        feed_permalink = get_permalink(feed)
        try:
            generator = FeedEntryGenerator(category_id, feed_id, feed_title,
                                           feed_permalink, it, now(), read,
                                           starred)
            generator.set_iterator(entry_after)
        except StopIteration:
            return jsonify(
                title=feed_title,
                entries=[],
                next_url=None,
                read_url=url_for('read_all_entries',
                                 feed_id=feed_id,
                                 last_updated=(updated_at or
                                               now()).isoformat(),
                                 _external=True),
                crawl_url=crawl_url
            )
    save_entry_generators(url_token, generator)
    tidy_generators_up()
    entries = generator.get_entries()
    if len(entries) < app.config['PAGE_SIZE']:
        next_url = None
        if not entries:
            remove_entry_generator(url_token)
    else:
        next_url = make_next_url(
            category_id,
            url_token,
            entries[-1]['entry_id'],
            read,
            starred,
            feed_id
        )
    response = jsonify(
        title=text_type(feed.title),
        entries=entries,
        next_url=next_url,
        read_url=url_for('read_all_entries',
                         feed_id=feed_id,
                         last_updated=(updated_at or now()).isoformat(),
                         _external=True),
        crawl_url=crawl_url
    )
    if feed.__revision__:
        response.last_modified = updated_at
    return response


class CategoryEntryGenerator():

    def __init__(self):
        self.generators = []

    def add(self, feed_entry_generator):
        if not isinstance(feed_entry_generator, FeedEntryGenerator):
            raise TypeError(
                'feed_entry_generator must be a subtype of'
                '{0.__module__}.{0.__name__}, not {1!r}'.format(
                    FeedEntryGenerator, feed_entry_generator)
            )
        self.generators.append(feed_entry_generator)

    def sort_generators(self):
        self.generators = sorted(self.generators, key=lambda generator:
                                 generator.entry.updated_at, reverse=True)

    def remove_if_iterator_ends(self, generator):
        try:
            generator.find_next_entry()
        except StopIteration:
            self.generators.remove(generator)

    def set_generators(self, entry_after, time_after):
        empty_generators = []
        for generator in self.generators:
            while (self.entry_newer_than_timestamp(generator, time_after) or
                   self.entry_same_as_latest_entry(generator, entry_after)):
                try:
                    generator.find_next_entry()
                except StopIteration:
                    empty_generators.append(generator)
                    break
        for generator in empty_generators:
            self.generators.remove(generator)
        self.sort_generators()

    def entry_newer_than_timestamp(self, generator, time_after):
        return (time_after and
                generator.entry.updated_at > Rfc3339().decode(time_after))

    def entry_same_as_latest_entry(self, generator, entry_id):
        return generator.entry.id == entry_id

    def find_next_generator(self):
        while self.generators:
            self.sort_generators()
            latest = self.generators[0]
            yield latest
            self.remove_if_iterator_ends(latest)

    def get_entries(self):
        entries = []
        generator_generator = self.find_next_generator()
        while len(entries) < app.config['PAGE_SIZE']:
            try:
                generator = next(generator_generator)
                entry_data = generator.get_entry_data()
                entries.append(entry_data)
            except StopIteration:
                return entries
        self.remove_if_iterator_ends(generator)
        return entries


@app.route('/entries/', defaults={'category_id': ''})
@app.route('/<path:category_id>/entries/')
def category_entries(category_id):
    category = transaction.get_category(category_id)
    generator = None
    url_token, entry_after, read, starred = get_optional_args()
    if url_token:
        try:
            generator = get_entry_generator(url_token)
        except IteratorNotFound:
            pass
    else:
        url_token = text_type(now())
    if not generator:
        subscriptions = category.recursive_subscriptions
        generator = CategoryEntryGenerator()
        if entry_after:
            id_after, time_after = entry_after.split('@')
        else:
            time_after = None
            id_after = None
        for subscription in subscriptions:
            try:
                feed = transaction.get_feed(subscription.feed_id)
            except FeedNotFound:
                continue
            feed_title = text_type(feed.title)
            it = iter(feed.entries)
            feed_permalink = get_permalink(feed)
            try:
                child = FeedEntryGenerator(category_id, subscription.feed_id,
                                           feed_title, feed_permalink, it,
                                           now(), read, starred)
            except StopIteration:
                continue
            generator.add(child)
        generator.set_generators(id_after, time_after)
    save_entry_generators(url_token, generator)
    tidy_generators_up()
    entries = generator.get_entries()
    if not entries or len(entries) < app.config['PAGE_SIZE']:
        next_url = None
        if not entries:
            remove_entry_generator(url_token)
    else:
        entry_after = entries[-1]['entry_id'] + '@' + entries[-1]['updated']
        next_url = make_next_url(category_id, url_token, entry_after, read,
                                 starred)

    # FIXME: use Entry.updated_at instead of from json data.
    codec = Rfc3339()
    last_updated_at = ''
    if len(entries) and not entry_after:
        last_updated_at = max(codec.decode(x['updated'])
                              for x in entries).isoformat()

    if worker.is_running():
        crawl_url = url_for('update_entries', category_id=category_id),
    else:
        crawl_url = None
    return jsonify(
        title=category_id.split('/')[-1][1:] or app.config['ALLFEED'],
        entries=entries,
        read_url=url_for('read_all_entries', category_id=category_id,
                         last_updated=last_updated_at,
                         _external=True),
        crawl_url=crawl_url,
        next_url=next_url
    )


@app.route('/feeds/<feed_id>/entries/', defaults={'category_id': ''},
           methods=['PUT'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/', methods=['PUT'])
@app.route('/entries/', defaults={'category_id': ''}, methods=['PUT'])
@app.route('/<path:category_id>/entries/', methods=['PUT'])
def update_entries(category_id, feed_id=None):
    if worker.is_running():
        category = transaction.get_category(category_id)
        worker.add_job(category, feed_id)
        r = jsonify()
        r.status_code = 202
        return r
    else:
        raise WorkerNotRunning('Worker thread is not running.')


def find_feed_and_entry(feed_id, entry_id):
    feed = transaction.get_feed(feed_id)
    feed_permalink = get_permalink(feed)
    for entry in feed.entries:
        entry_permalink = get_permalink(entry)
        if entry_id == get_hash(entry.id):
            return feed, feed_permalink, entry, entry_permalink
    raise EntryNotFound('The entry is not reachable')


@app.route('/feeds/<feed_id>/entries/<entry_id>/',
           defaults={'category_id': ''})
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/')
def feed_entry(category_id, feed_id, entry_id):
    feed, feed_permalink, entry, entry_permalink = \
        find_feed_and_entry(feed_id, entry_id)
    content = entry.content or entry.summary
    if content is not None:
        content = content.sanitized_html

    entry_data = {
        'title': text_type(entry.title),
        'content': content,
        'updated': text_type(entry.updated_at),
        'permalink': entry_permalink or None,
        }
    feed_data = {
        'title': text_type(feed.title),
        'permalink': feed_permalink or None
    }
    add_urls(
        entry_data,
        ['read_url', 'unread_url', 'star_url', 'unstar_url'],
        category_id,
        feed_id,
        entry_id
    )
    add_urls(
        feed_data,
        ['entries_url'],
        category_id,
        feed_id
    )
    entry_data['feed'] = feed_data
    return jsonify(entry_data)


@app.route('/feeds/<feed_id>/entries/<entry_id>/read/',
           defaults={'category_id': ''}, methods=['PUT'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/read/',
           methods=['PUT'])
def read_entry(category_id, feed_id, entry_id):
    feed, _, entry, _ = find_feed_and_entry(feed_id, entry_id)
    entry.read = True
    transaction.update_feed(feed_id, feed)
    transaction.save()
    return jsonify()


@app.route('/feeds/<feed_id>/entries/<entry_id>/read/',
           defaults={'category_id': ''}, methods=['DELETE'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/read/',
           methods=['DELETE'])
def unread_entry(category_id, feed_id, entry_id):
    feed, _, entry, _ = find_feed_and_entry(feed_id, entry_id)
    entry.read = False
    transaction.update_feed(feed_id, feed)
    transaction.save()
    return jsonify()


@app.route('/feeds/<feed_id>/entries/read/', methods=['PUT'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/read/',
           methods=['PUT'])
@app.route('/entries/read/', methods=['PUT'])
@app.route('/<path:category_id>/entries/read/', methods=['PUT'])
def read_all_entries(category_id='', feed_id=None):
    if feed_id:
        feed_ids = [feed_id]
    else:
        category = transaction.get_category(category_id)
        feed_ids = [sub.feed_id for sub in category.recursive_subscriptions]

    try:
        codec = Rfc3339()
        last_updated = codec.decode(request.args.get('last_updated'))
    except:
        last_updated = None

    for feed_id in feed_ids:
        feed = transaction.get_feed(feed_id)
        for entry in feed.entries:
            if not last_updated or entry.updated_at <= last_updated:
                entry.read = True
        transaction.update_feed(feed_id, feed)
        transaction.save()
    return jsonify()


@app.route('/feeds/<feed_id>/entries/<entry_id>/star/',
           defaults={'category_id': ''}, methods=['PUT'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/star/',
           methods=['PUT'])
def star_entry(category_id, feed_id, entry_id):
    feed, _, entry, _ = find_feed_and_entry(feed_id, entry_id)
    entry.starred = True
    transaction.update_feed(feed_id, feed)
    transaction.save()
    return jsonify()


@app.route('/feeds/<feed_id>/entries/<entry_id>/star/',
           defaults={'category_id': ''}, methods=['DELETE'])
@app.route('/<path:category_id>/feeds/<feed_id>/entries/<entry_id>/star/',
           methods=['DELETE'])
def unstar_entry(category_id, feed_id, entry_id):
    feed, _, entry, _ = find_feed_and_entry(feed_id, entry_id)
    entry.starred = False
    transaction.update_feed(feed_id, feed)
    transaction.save()
    return jsonify()
