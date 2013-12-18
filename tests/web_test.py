try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import datetime
import hashlib
try:
    import httplib
except ImportError:
    from http import client as httplib
import traceback
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from flask import json, url_for
from libearth.compat import binary
from libearth.crawler import crawl
from libearth.feed import Entry, Feed, Mark, Person, Text
from libearth.repository import FileSystemRepository
from libearth.schema import read
from libearth.session import Session
from libearth.stage import Stage
from libearth.subscribe import Category, Subscription, SubscriptionList
from libearth.tz import utc
from pytest import fixture, mark
from werkzeug.urls import url_encode

from earthreader.web import (app, crawling_queue, get_hash, spawn_worker,
                             entry_generators)


@app.errorhandler(400)
def bad_request_handler_for_testing(exception):
    """Custom error handler of :http:statuscode:`400` for unit testing
    to know how it's going in the application.

    """
    traceback.print_exc()
    return (
        traceback.format_exc(),
        400,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


@app.errorhandler(500)
def server_error_handler_for_testing(exception):
    """Custom error handler of :http:statuscode:`500` for unit testing
    to know how it's going in the application.

    """
    traceback.print_exc()
    return (
        traceback.format_exc(),
        500,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


def get_url(endpoint, **values):
    with app.test_request_context():
        return url_for(endpoint, **values)


feed_one = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed One</title>
    <id>http://feedone.com/feed/atom/</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
    <link type="text/html" rel="alternate" href="http://feedone.com" />
    <entry>
        <title>Feed One: Entry One</title>
        <id>http://feedone.com/feed/atom/1/</id>
        <updated>2013-08-19T07:49:20+07:00</updated>
        <published>2013-08-19T07:49:20+07:00</published>
        <content>This is content of Entry One in Feed One</content>
    </entry>
    <entry>
        <title>Feed One: Entry Two</title>
        <id>http://feedone.com/feed/atom/2/</id>
        <updated>2013-10-19T07:49:20+07:00</updated>
        <published>2013-10-19T07:49:20+07:00</published>
        <content>This is content of Entry Two in Feed One</content>
    </entry>
</feed>
'''

feed_two = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Two</title>
    <id>http://feedtwo.com/feed/atom/</id>
    <updated>2013-08-20T07:49:20+07:00</updated>
    <link type="text/html" rel="alternate" href="http://feedtwo.com" />
    <entry>
        <title>Feed Two: Entry One</title>
        <id>http://feedtwo.com/feed/atom/1/</id>
        <updated>2013-08-20T07:49:20+07:00</updated>
        <published>2013-08-20T07:49:20+07:00</published>
        <content>This is content of Entry One in Feed Two</content>
    </entry>
</feed>
'''


feed_three = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Three</title>
    <id>http://feedthree.com/feed/atom/</id>
    <updated>2013-08-21T07:49:20+07:00</updated>
    <link type="text/html" rel="alternate" href="http://feedthree.com" />
    <entry>
        <title>Feed Three: Entry One</title>
        <id>http://feedthree.com/feed/atom/1/</id>
        <updated>2013-08-21T07:49:20+07:00</updated>
        <published>2013-08-21T07:49:20+07:00</published>
        <content>This is content of Entry One in Feed Three</content>
    </entry>
</feed>
'''


feed_four = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Four</title>
    <id>http://feedfour.com/feed/atom/</id>
    <updated>2013-08-22T07:49:20+07:00</updated>
    <link type="text/html" rel="alternate" href="http://feedfour.com" />
    <entry>
        <title>Feed Four: Entry One</title>
        <id>http://feedfour.com/feed/atom/1/</id>
        <updated>2013-08-22T07:49:20+07:00</updated>
        <published>2013-08-22T07:49:20+07:00</published>
        <content>This is content of Entry One in Feed Four</content>
    </entry>
</feed>
'''


feed_to_add = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Five</title>
    <id>http://feedfive.com/feed/atom/</id>
    <updated>2013-08-23T07:49:20+07:00</updated>
    <link type="text/html" rel="alternate" href="http://feedfive.com" />
    <entry>
        <title>Feed Five: Entry One</title>
        <id>http://feedfive.com/feed/atom/1/</id>
        <updated>2013-08-22T07:49:20+07:00</updated>
        <published>2013-08-22T07:49:20+07:00</published>
        <content>This is content of Entry One in Feed Four</content>
    </entry>
</feed>
'''


def get_feed_urls(category, urls=[]):
    for child in category:
        if isinstance(child, Subscription):
            urls.append(child.feed_uri)
        elif isinstance(child, Category):
            get_feed_urls(child, urls)
    return urls


mock_urls = {
    'http://feedone.com/feed/atom/': (200, 'application+xml', feed_one),
    'http://feedtwo.com/feed/atom/': (200, 'application+xml', feed_two),
    'http://feedthree.com/feed/atom/': (200, 'application+xml', feed_three),
    'http://feedfour.com/feed/atom/': (200, 'application+xml', feed_four),
    'http://feedfive.com/feed/atom/': (200, 'application+xml', feed_to_add),
}


class TestHTTPHandler(urllib2.HTTPHandler):

    def http_open(self, req):
        url = req.get_full_url()
        try:
            status_code, mimetype, content = mock_urls[url]
        except KeyError:
            return urllib2.HTTPHandler.http_open(self, req)
        resp = urllib2.addinfourl(StringIO(content),
                                  {'content-type': mimetype},
                                  url)
        resp.code = status_code
        resp.msg = httplib.responses[status_code]
        return resp


my_opener = urllib2.build_opener(TestHTTPHandler)
urllib2.install_opener(my_opener)


@fixture
def fx_test_stage(tmpdir):
    session = Session()
    repo = FileSystemRepository(str(tmpdir))
    stage = Stage(session, repo)
    app.config['STAGE'] = stage
    return stage


@fixture
def xmls(request, fx_test_stage):
    stage = fx_test_stage
    subscriptions = SubscriptionList()
    categoryone = Category(label='categoryone', _title='categoryone')
    categorytwo = Category(label='categorytwo', _title='categorytwo')
    categorythree = Category(label='categorythree', _title='categorythree')
    subscriptions.add(categoryone)
    subscriptions.add(categorythree)
    categoryone.add(categorytwo)
    pair = {
        'http://feedone.com/feed/atom/': categoryone,
        'http://feedtwo.com/feed/atom/': categorytwo,
        'http://feedthree.com/feed/atom/': subscriptions,
        'http://feedfour.com/feed/atom/': categorythree
    }
    generator = crawl(pair.keys(), 4)
    with stage:
        for feed_url, feed, hints in generator:
            sub = pair[feed_url].subscribe(feed)
            stage.feeds[sub.feed_id] = feed
        stage.subscriptions = subscriptions


def empty_queue():
    with crawling_queue.mutex:
        crawling_queue.queue.clear()


@fixture
def fx_crawler(request):
    empty_queue()
    spawn_worker()

    def terminate():
        empty_queue()
        crawling_queue.put((0, 'terminate'))

    request.addfinalizer(terminate)


@fixture
def fx_crawling_queue(request):
    request.addfinalizer(empty_queue)


def test_all_feeds(xmls):
    with app.test_client() as client:
        FEED_ONE_ID = get_hash('http://feedone.com/feed/atom/')
        FEED_TWO_ID = get_hash('http://feedtwo.com/feed/atom/')
        FEED_THREE_ID = get_hash('http://feedthree.com/feed/atom/')
        FEED_FOUR_ID = get_hash('http://feedfour.com/feed/atom/')
        # /
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        root_feeds = result['feeds']
        root_categories = result['categories']
        assert root_feeds[0]['title'] == 'Feed Three'
        assert root_feeds[0]['path'] == '/feeds/' + FEED_THREE_ID
        assert root_categories[0]['title'] == 'categoryone'
        assert root_categories[0]['path'] == '-categoryone'
        assert root_categories[1]['title'] == 'categorythree'
        assert root_categories[1]['path'] == '-categorythree'
        # /feedthree
        feed_url = root_feeds[0]['entries_url']
        assert feed_url == \
            url_for(
                'feed_entries',
                feed_id=FEED_THREE_ID,
                _external=True
            )
        r = client.get(feed_url)
        assert r.status_code == 200
        result = json.loads(r.data)
        entries = result['entries']
        assert entries[0]['title'] == 'Feed Three: Entry One'
        assert entries[0]['entry_url'] == \
            url_for(
                'feed_entry',
                feed_id=FEED_THREE_ID,
                entry_id=get_hash('http://feedthree.com/feed/atom/1/'),
                _external=True,
            )
        assert entries[0]['updated'] == '2013-08-21T00:49:20Z'
        r = client.get(entries[0]['entry_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'Feed Three: Entry One'
        assert result['content'] == \
            'This is content of Entry One in Feed Three'
        assert result['updated'] == '2013-08-21 07:49:20+07:00'
        # /categoryone
        category_url = root_categories[0]['feeds_url']
        assert category_url == \
            url_for(
                'feeds',
                category_id='-categoryone',
                _external=True
            )
        one_r = client.get(root_categories[0]['feeds_url'])
        assert one_r.status_code == 200
        one_result = json.loads(one_r.data)
        one_feeds = one_result['feeds']
        one_categories = one_result['categories']
        assert one_feeds[0]['title'] == 'Feed One'
        assert one_feeds[0]['path'] == '-categoryone/feeds/' + FEED_ONE_ID
        assert one_categories[0]['title'] == 'categorytwo'
        # /categoryone/feedone
        feed_url = one_feeds[0]['entries_url']
        feed_id = get_hash('http://feedone.com/feed/atom/')
        assert feed_url == \
            url_for(
                'feed_entries',
                category_id='-categoryone',
                feed_id=feed_id,
                _external=True
            )
        r = client.get(feed_url)
        assert r.status_code == 200
        result = json.loads(r.data)
        entries = result['entries']
        assert entries[0]['title'] == 'Feed One: Entry Two'
        assert entries[0]['entry_url'] == \
            url_for(
                'feed_entry',
                category_id='-categoryone',
                feed_id=feed_id,
                entry_id=get_hash('http://feedone.com/feed/atom/2/'),
                _external=True
            )
        assert entries[0]['updated'] == '2013-10-19T00:49:20Z'
        assert entries[1]['title'] == 'Feed One: Entry One'
        assert entries[1]['entry_url'] == \
            url_for(
                'feed_entry',
                category_id='-categoryone',
                feed_id=feed_id,
                entry_id=get_hash('http://feedone.com/feed/atom/1/'),
                _external=True
            )
        assert entries[1]['updated'] == '2013-08-19T00:49:20Z'
        r = client.get(entries[0]['entry_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'Feed One: Entry Two'
        assert result['content'] == \
            'This is content of Entry Two in Feed One'
        assert result['updated'] == '2013-10-19 07:49:20+07:00'
        # /categoryone/categorytwo
        two_r = client.get(one_categories[0]['feeds_url'])
        assert two_r.status_code == 200
        two_result = json.loads(two_r.data)
        two_feeds = two_result['feeds']
        two_categories = two_result['categories']
        assert two_feeds[0]['title'] == 'Feed Two'
        assert two_feeds[0]['path'] == '-categoryone/-categorytwo/feeds/' + \
            FEED_TWO_ID
        assert len(two_categories) == 0
        # /categoryone/categorytwo/feedtwo
        category_url = one_categories[0]['feeds_url']
        assert category_url == \
            url_for(
                'feeds',
                category_id='-categoryone/-categorytwo',
                _external=True
            )

        feed_url = two_feeds[0]['entries_url']
        feed_id = get_hash('http://feedtwo.com/feed/atom/')
        assert feed_url == \
            url_for(
                'feed_entries',
                category_id='-categoryone/-categorytwo',
                feed_id=feed_id,
                _external=True
            )
        r = client.get(feed_url)
        assert r.status_code == 200
        result = json.loads(r.data)
        entries = result['entries']
        assert entries[0]['title'] == 'Feed Two: Entry One'
        assert entries[0]['entry_url'] == \
            url_for(
                'feed_entry',
                category_id='-categoryone/-categorytwo',
                feed_id=feed_id,
                entry_id=get_hash('http://feedtwo.com/feed/atom/1/'),
                _external=True
            )
        assert entries[0]['updated'] == '2013-08-20T00:49:20Z'
        r = client.get(entries[0]['entry_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'Feed Two: Entry One'
        assert result['content'] == \
            'This is content of Entry One in Feed Two'
        assert result['updated'] == '2013-08-20 07:49:20+07:00'
        # categorythree
        category_url = root_categories[1]['feeds_url']
        assert category_url == \
            url_for(
                'feeds',
                category_id='-categorythree',
                _external=True
            )
        three_r = client.get(root_categories[1]['feeds_url'])
        assert three_r.status_code == 200
        three_result = json.loads(three_r.data)
        three_feeds = three_result['feeds']
        three_categories = three_result['categories']
        assert three_feeds[0]['title'] == 'Feed Four'
        assert three_feeds[0]['path'] == '-categorythree/feeds/' + FEED_FOUR_ID
        assert len(three_categories) == 0
        # /categorythree/feedfour
        feed_url = three_feeds[0]['entries_url']
        feed_id = get_hash('http://feedfour.com/feed/atom/')
        assert feed_url == \
            url_for(
                'feed_entries',
                category_id='-categorythree',
                feed_id=feed_id,
                _external=True
            )
        r = client.get(feed_url)
        assert r.status_code == 200
        result = json.loads(r.data)
        entries = result['entries']
        assert entries[0]['title'] == 'Feed Four: Entry One'
        assert entries[0]['entry_url'] == \
            url_for(
                'feed_entry',
                category_id='-categorythree',
                feed_id=feed_id,
                entry_id=get_hash('http://feedfour.com/feed/atom/1/'),
                _external=True
            )
        assert entries[0]['updated'] == '2013-08-22T00:49:20Z'
        r = client.get(entries[0]['entry_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'Feed Four: Entry One'
        assert result['content'] == \
            'This is content of Entry One in Feed Four'
        assert result['updated'] == '2013-08-22 07:49:20+07:00'


def test_invalid_path(xmls):
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://feedone.com/feed/atom/')).hexdigest()
        r = client.get('/non-exist-category/feeds/' + feed_id + '/entries/')
        result = json.loads(r.data)
        assert r.status_code == 404
        assert result['error'] == 'category-id-invalid'


def test_add_feed(xmls, fx_test_stage):
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(url='http://feedfive.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][1]['title'] == 'Feed Five'
        with fx_test_stage as stage:
            opml = stage.subscriptions
        assert opml.children[3]._title == 'Feed Five'


def test_add_feed_in_category(xmls, fx_test_stage):
    with app.test_client() as client:
        r = client.get('/-categoryone/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        add_feed_url = result['categories'][0]['add_feed_url']
        r = client.post(add_feed_url,
                        data=dict(url='http://feedfive.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'Feed Two'
        assert result['feeds'][1]['title'] == 'Feed Five'
        with fx_test_stage as stage:
            subscriptions = stage.subscriptions
        categoryone = subscriptions.categories['categoryone']
        categorytwo = categoryone.categories['categorytwo']
        assert len(categorytwo.subscriptions) == 2


def test_add_category(xmls, fx_test_stage):
    with app.test_client() as client:
        r = client.post('/',
                        data=dict(title='addedcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['categories'][2]['title'] == 'addedcategory'
        with fx_test_stage as stage:
            subscriptions = stage.subscriptions
        assert subscriptions.categories['addedcategory'] is not None


def test_add_category_in_category(xmls, fx_test_stage):
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        add_category_url = result['categories'][0]['add_category_url']
        r = client.post(add_category_url,
                        data=dict(title='addedcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['categories'][1]['title'] == 'addedcategory'
        with fx_test_stage as stage:
            subscriptions = stage.subscriptions
        categoryone = subscriptions.categories['categoryone']
        assert categoryone.categories['addedcategory'] is not None


def test_add_category_without_opml(fx_test_stage):
    with app.test_client() as client:
        r = client.post('/',
                        data=dict(title='testcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['categories'][0]['title'] == 'testcategory'
        with fx_test_stage as stage:
            subscriptions = stage.subscriptions
        assert subscriptions.categories['testcategory'] is not None


def test_add_feed_without_opml(fx_test_stage):
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(url='http://feedone.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'Feed One'
        with fx_test_stage as stage:
            subscriptions = stage.subscriptions
        assert len(subscriptions.subscriptions) == 1


def test_delete_feed(xmls, fx_test_stage):
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://feedthree.com/feed/atom/')).hexdigest()
        r = client.delete('/feeds/' + feed_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        for child in result['feeds']:
            assert child['title'] != 'Feed Three'


def test_delete_feed_in_category(xmls):
    with app.test_client() as client:
        r = client.get('/-categoryone/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['feeds']) == 1
        remove_feed_url = result['feeds'][0]['remove_feed_url']
        r = client.delete(remove_feed_url)
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['feeds']) == 0


def test_delete_non_exists_feed(xmls):
    with app.test_client() as client:
        r = client.delete('/feeds/non-exists-feed/')
        assert r.status_code == 400
        result = json.loads(r.data)
        assert result['error'] == 'feed-not-found-in-path'


def test_delete_category_in_root(xmls):
    with app.test_client() as client:
        r = client.delete('/-categoryone/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result == json.loads(client.get('/feeds/').data)
        for child in result['categories']:
            assert not child['title'] == 'categoryone'


def test_delete_category_in_category(xmls):
    with app.test_client() as client:
        r = client.get('/-categoryone/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        remove_category_url = result['categories'][0]['remove_category_url']
        r = client.delete(remove_category_url)
        assert r.status_code == 200
        result = json.loads(client.get('/-categoryone/feeds/').data)
        for child in result['categories']:
            assert not child['title'] == 'categorytwo'


def test_category_all_entries(xmls):
    with app.test_client() as client:
        r = client.get('/-categoryone/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'categoryone'
        assert result['entries'][0]['title'] == 'Feed One: Entry Two'
        entry_url = result['entries'][0]['entry_url']
        r = client.get(entry_url)
        assert r.status_code == 200
        two_result = json.loads(r.data)
        assert two_result['title'] == 'Feed One: Entry Two'
        assert two_result['content'] == \
            'This is content of Entry Two in Feed One'
        assert two_result['updated'] == '2013-10-19 07:49:20+07:00'
        assert two_result['permalink'] == 'http://feedone.com/feed/atom/2/'
        assert two_result['feed']['title'] == 'Feed One'
        assert two_result['feed']['permalink'] == \
            'http://feedone.com'
        feed_id = get_hash('http://feedone.com/feed/atom/')
        assert two_result['feed']['entries_url'] == \
            url_for(
                'feed_entries',
                category_id='-categoryone',
                feed_id=feed_id,
                _external=True
            )
        assert result['entries'][1]['title'] == 'Feed Two: Entry One'
        entry_url = result['entries'][1]['entry_url']
        r = client.get(entry_url)
        assert r.status_code == 200
        one_result = json.loads(r.data)
        assert one_result['content'] == \
            'This is content of Entry One in Feed Two'
        r = client.get('/-categoryone/-categorytwo/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'categorytwo'
        assert result['entries'][0]['title'] == 'Feed Two: Entry One'


def test_empty_category_all_entries(xmls):
    with app.test_client() as client:
        r = client.post('/', data=dict(title='test'))
        assert r.status_code == 200
        r = client.get('/-test/entries/')
        assert r.status_code == 200


@fixture
def fx_xml_for_update(xmls, request):
    updated_feed_two = '''
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title type="text">Feed Two</title>
        <id>http://feedtwo.com/feed/atom/</id>
        <updated>2013-11-20T07:49:20+07:00</updated>
        <link type="text/html" rel="alternate" href="http://feedtwo.com" />
        <entry>
            <title>Feed Two: Entry Two</title>
            <id>http://feedtwo.com/feed/atom/2/</id>
            <updated>2013-11-20T07:49:20+07:00</updated>
            <published>2013-11-20T07:49:20+07:00</published>
            <content>This is content of Entry Two in Feed Two</content>
        </entry>
        <entry>
            <title>Feed Two: Entry One</title>
            <id>http://feedtwo.com/feed/atom/1/</id>
            <updated>2013-08-20T07:49:20+07:00</updated>
            <published>2013-08-20T07:49:20+07:00</published>
            <content>This is content of Entry One in Feed Two</content>
        </entry>
    </feed>
    '''
    updated_feed_three = '''
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title type="text">Feed Three</title>
        <id>http://feedthree.com/feed/atom/</id>
        <updated>2013-11-21T07:49:20+07:00</updated>
        <link type="text/html" rel="alternate" href="http://feedthree.com" />
        <entry>
            <title>Feed Three: Entry Two</title>
            <id>http://feedthree.com/feed/atom/2/</id>
            <updated>2013-11-21T07:49:20+07:00</updated>
            <published>2013-11-21T07:49:20+07:00</published>
            <content>This is content of Entry Two in Feed Three</content>
        </entry>
        <entry>
            <title>Feed Three: Entry One</title>
            <id>http://feedthree.com/feed/atom/1/</id>
            <updated>2013-08-21T07:49:20+07:00</updated>
            <published>2013-08-21T07:49:20+07:00</published>
            <content>This is content of Entry One in Feed Three</content>
        </entry>
    </feed>
    '''

    mock_urls = {
        'http://feedone.com/feed/atom/': (200, 'application+xml', feed_one),
        'http://feedtwo.com/feed/atom/': (200, 'application+xml',
                                          updated_feed_two),
        'http://feedthree.com/feed/atom/': (200, 'application+xml',
                                            updated_feed_three),
        'http://feedfour.com/feed/atom/': (200, 'application+xml', feed_four),
        'http://feedfive.com/feed/atom/': (200, 'application+xml', feed_to_add),
    }

    class TestHTTPHandler2(urllib2.HTTPHandler):

        def http_open(self, req):
            url = req.get_full_url()
            try:
                status_code, mimetype, content = mock_urls[url]
            except KeyError:
                return urllib2.HTTPHandler.http_open(self, req)
            resp = urllib2.addinfourl(StringIO(content),
                                      {'content-type': mimetype},
                                      url)
            resp.code = status_code
            resp.msg = httplib.responses[status_code]
            return resp

    my_opener2 = urllib2.build_opener(TestHTTPHandler2)
    urllib2.install_opener(my_opener2)

    def finalizer():
        urllib2.install_opener(my_opener)

    request.addfinalizer(finalizer)


def test_update_feed_entries(fx_xml_for_update, fx_test_stage,
                             fx_crawling_queue):
    with app.test_client() as client:
        feed_two_id = get_hash('http://feedtwo.com/feed/atom/')
        with fx_test_stage as stage:
            assert len(stage.feeds[feed_two_id].entries) == 1

        assert crawling_queue.qsize() == 0
        r = client.put(
            get_url(
                'update_entries',
                category_id='-categoryone/-categorytwo',
                feed_id=feed_two_id
            )
        )
        assert r.status_code == 202
        assert crawling_queue.qsize() == 1


def test_update_category_entries(fx_xml_for_update, fx_test_stage,
                                 fx_crawling_queue):
    with app.test_client() as client:
        feed_two_id = get_hash('http://feedtwo.com/feed/atom/')
        feed_three_id = get_hash('http://feedthree.com/feed/atom/')
        with fx_test_stage as stage:
            assert len(stage.feeds[feed_two_id].entries) == 1
            assert len(stage.feeds[feed_three_id].entries) == 1
        r = client.put('/entries/')
        assert r.status_code == 202
        assert crawling_queue.qsize() == 1


def test_entry_read_unread(xmls, fx_test_stage):
    with app.test_client() as client:
        feed_three_id = get_hash('http://feedthree.com/feed/atom/')
        test_entry_id = get_hash('http://feedthree.com/feed/atom/1/')
        with fx_test_stage as stage:
            assert not stage.feeds[feed_three_id].entries[0].read
        r = client.get('/feeds/' + feed_three_id + '/entries/' +
                       test_entry_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        r = client.put(result['read_url'])
        assert r.status_code == 200
        with fx_test_stage as stage:
            assert stage.feeds[feed_three_id].entries[0].read
        r = client.delete(result['unread_url'])
        assert r.status_code == 200
        with fx_test_stage as stage:
            assert not stage.feeds[feed_three_id].entries[0].read


def test_entry_star_unstar(xmls, fx_test_stage):
    with app.test_client() as client:
        feed_three_id = get_hash('http://feedthree.com/feed/atom/')
        test_entry_id = get_hash('http://feedthree.com/feed/atom/1/')
        with fx_test_stage as stage:
            assert not stage.feeds[feed_three_id].entries[0].read
        r = client.get('/feeds/' + feed_three_id + '/entries/' +
                       test_entry_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        r = client.put(result['star_url'])
        assert r.status_code == 200
        with fx_test_stage as stage:
            assert stage.feeds[feed_three_id].entries[0].starred
        r = client.delete(result['unstar_url'])
        assert r.status_code == 200
        with fx_test_stage as stage:
            assert not stage.feeds[feed_three_id].entries[0].starred


opml_for_filtering = '''
<opml version="1.0">
  <head>
    <title>test opml</title>
  </head>
  <body>
    <outline type="atom" text="Feed Three" title="Feed Three"
    xmlUrl="http://feedthree.com/feed/atom/" />
  </body>
</opml>
'''


@fixture
def fx_filtering_entries(fx_test_stage):
    authors = [Person(name='vio')]
    now = datetime.datetime(2013, 10, 30, 20, 55, 30, tzinfo=utc)
    feed = Feed(id='http://feedone.com/feed/atom/', authors=authors,
                title=Text(value='Feed One'),
                updated_at=now)
    for i in range(10):
        feed.entries.append(
            Entry(id='http://feedone.com/feed/atom/' + str(i) + '/',
                  authors=authors,
                  title=Text(value=str(i + 1)),
                  updated_at=now + datetime.timedelta(days=1) * i)
        )
    for i in range(5):
        feed.entries[i].read = Mark(marked=True, updated_at=now)
    for i in range(3, 7):
        feed.entries[i].starred = Mark(marked=True, updated_at=now)
    with fx_test_stage as stage:
        stage.feeds[get_hash('http://feedone.com/feed/atom/')] = feed
        stage.subscriptions = read(SubscriptionList, opml_for_filtering)


@mark.parametrize(('read', 'starred', 'expected_entries'), [
    (True, True, [4, 5]),
    (False, True, [6, 7]),
    (None, True, [4, 5, 6, 7]),
    (True, False, [1, 2, 3]),
    (False, False, [8, 9, 10]),
    (None, False, [1, 2, 3, 8, 9, 10]),
    (True, None, [1, 2, 3, 4, 5]),
    (False, None, [6, 7, 8, 9, 10]),
    (None, None, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
])
def test_entries_filtering(read, starred, expected_entries,
                           fx_filtering_entries, fx_test_stage):
    feed_id = get_hash('http://feedone.com/feed/atom/')
    options = {}
    if read is not None:
        options['read'] = str(read)
    if starred is not None:
        options['starred'] = str(starred)
    qs = url_encode(options)
    with app.test_client() as client:
        r = client.get('/feeds/' + feed_id + '/entries/?' + qs)
        entries = json.loads(r.data)['entries']
        assert (frozenset(int(e['title']) for e in entries) ==
                frozenset(expected_entries))


opml_with_non_exist_feed = '''
<opml version="1.0">
  <head>
    <title>test opml</title>
  </head>
  <body>
    <outline text="categoryone" title="categoryone">
        <outline type="atom" text="Feed One" title="Feed One"
        xmlUrl="http://feedone.com/feed/atom/" />
        <outline type="atom" text="Non Exist" title="Non Exist"
        xmlUrl="Non Exsist" />
    </outline>
  </body>
</opml>
'''


@fixture
def fx_non_exist_opml(fx_test_stage):
    feed_urls = ['http://feedone.com/feed/atom/']
    generator = crawl(feed_urls, 1)
    for result in generator:
        feed_data = result[1]
        feed_url = result[0]
        feed_id = get_hash(feed_url)
        with fx_test_stage as stage:
            stage.feeds[feed_id] = feed_data
    with fx_test_stage as stage:
        stage.subscriptions = read(SubscriptionList, opml_with_non_exist_feed)


def test_non_exist_feed(fx_non_exist_opml):
    with app.test_client() as client:
        r = client.get('/-categoryone/entries/')
        assert r.status_code == 200
        with_non_exist_feed_result = json.loads(r.data)
        feed_one_id = get_hash('http://feedone.com/feed/atom/')
        r = client.get('/-categoryone/feeds/' + feed_one_id + '/entries/')
        assert r.status_code == 200
        feed_one_result = json.loads(r.data)
        assert len(with_non_exist_feed_result['entries']) == \
            len(feed_one_result['entries']) == 2
        non_exist_id = get_hash('Non Exist')
        r = client.get('/-categoryone/feeds/' + non_exist_id + '/entries/')
        assert r.status_code == 404


@fixture
def xmls_for_next(request, fx_test_stage):
    opml = '''
    <opml version="1.0">
      <head>
        <title>test opml</title>
      </head>
      <body>
        <outline text="categoryone" title="categoryone">
            <outline type="atom" text="Feed One" title="Feed One"
            xmlUrl="http://feedone.com/" />
            <outline type="atom" text="Feed Two" title="Feed Two"
            xmlUrl="http://feedtwo.com/" />
        </outline>
        <outline type="atom" text="Feed Three" title="Feed Three"
        xmlUrl="http://feedthree.com/" />
        <outline type="atom" text="Feed Four" title="Feed Three"
        xmlUrl="http://feedthree.com/" />
      </body>
    </opml>
    '''
    authors = [Person(name='vio')]
    feed_one = Feed(id='http://feedone.com/', authors=authors,
                    title=Text(value='Feed One'),
                    updated_at=datetime.datetime(2013, 10, 30, 20, 55, 30,
                                                 tzinfo=utc))
    feed_two = Feed(id='http://feedtwo.com/', authors=authors,
                    title=Text(value='Feed Two'),
                    updated_at=datetime.datetime(2013, 10, 30, 21, 55, 30,
                                                 tzinfo=utc))
    feed_three = Feed(id='http://feedthree.com/', authors=authors,
                      title=Text(value='Feed Three'),
                      updated_at=datetime.datetime(2013, 10, 30, 21, 55, 30,
                                                   tzinfo=utc))
    feed_four = Feed(id='http://feedfour.com/', authors=authors,
                     title=Text(value='Feed Four'),
                     updated_at=datetime.datetime(2013, 10, 30, 21, 55, 30,
                                                  tzinfo=utc))
    for i in range(25):
        feed_one.entries.append(
            Entry(id='http://feedone.com/' + str(24 - i),
                  authors=authors,
                  title=Text(value='Feed One: Entry ' + str(24 - i)),
                  updated_at=datetime.datetime(2013, 10, 30, 20, 55, 30,
                                               tzinfo=utc) +
                  datetime.timedelta(days=-1)*i)
        )
        feed_two.entries.append(
            Entry(id='http://feedtwo.com/' + str(24 - i),
                  authors=authors,
                  title=Text(value='Feed Two: Entry ' + str(24 - i)),
                  updated_at=datetime.datetime(2013, 10, 30, 19, 55, 30,
                                               tzinfo=utc) +
                  datetime.timedelta(days=-1)*i)
        )
    for i in range(20):
        feed_three.entries.append(
            Entry(id='http://feedthree.com/' + str(19 - i),
                  authors=authors,
                  title=Text(value='Feed Three: Entry ' + str(19 - i)),
                  updated_at=datetime.datetime(2013, 10, 30, 20, 55, 30,
                                               tzinfo=utc) +
                  datetime.timedelta(days=-1)*i)
        )
    for i in range(50):
        feed_four.entries.append(
            Entry(id='http://feedfour.com/' + str(49 - i),
                  authors=authors,
                  title=Text(value='Feed Four: Entry ' + str(49 - i)),
                  updated_at=datetime.datetime(2013, 10, 30, 20, 55, 30,
                                               tzinfo=utc) +
                  datetime.timedelta(days=-1)*i)
        )
    for i in range(5):
        feed_two.entries[i].read = True
        feed_two.entries[i+15].read = True
    for i in range(20, 50):
        feed_four.entries[i].read = True
    subscriptions = read(SubscriptionList, opml)
    with fx_test_stage as stage:
        stage.subscriptions = subscriptions
        stage.feeds[get_hash('http://feedone.com/')] = feed_one
        stage.feeds[get_hash('http://feedtwo.com/')] = feed_two
        stage.feeds[get_hash('http://feedthree.com/')] = feed_three
        stage.feeds[get_hash('http://feedfour.com/')] = feed_four


@mark.parametrize('make_empty', [True, False])
def test_feed_entries_next(make_empty, xmls_for_next):
    with app.test_client() as client:
        r = client.get('/-categoryone/feeds/' +
                       get_hash('http://feedone.com/') +
                       '/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 20
        assert result['entries'][-1]['title'] == 'Feed One: Entry 5'
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 5
        assert result['entries'][-1]['title'] == 'Feed One: Entry 0'
        assert not result['next_url']


@mark.parametrize('make_empty', [True, False])
def test_feed_with_20_entries(make_empty, xmls_for_next):
    with app.test_client() as client:
        r = client.get('/feeds/' + get_hash('http://feedthree.com/') +
                       '/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        assert r.status_code == 200
        result = json.loads(r.data)
        assert not result['entries']
        assert not result['next_url']


@mark.parametrize('make_empty', [True, False])
def test_category_entries_next(make_empty, xmls_for_next):
    with app.test_client() as client:
        r = client.get('/-categoryone/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 20
        assert result['entries'][-1]['title'] == 'Feed Two: Entry 15'
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        result = json.loads(r.data)
        assert len(result['entries']) == 20
        assert result['entries'][-1]['title'] == 'Feed Two: Entry 5'
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        result = json.loads(r.data)
        assert len(result['entries']) == 10
        assert result['entries'][-1]['title'] == 'Feed Two: Entry 0'


@mark.parametrize('make_empty', [True, False])
def test_feed_entries_filtering(make_empty, xmls_for_next):
    with app.test_client() as client:
        feed_id = get_hash('http://feedfour.com/')
        r = client.get('/feeds/' + feed_id + '/entries/?read=False')
        assert r.status_code == 200
        result = json.loads(r.data)
        for entry in result['entries']:
            assert entry['read'] is False
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        result = json.loads(r.data)
        for entry in result['entries']:
            assert entry['read'] is False


@mark.parametrize('make_empty', [True, False])
def test_category_entries_filtering(make_empty, xmls_for_next):
    with app.test_client() as client:
        r = client.get('/-categoryone/entries/?read=False')
        result = json.loads(r.data)
        for entry in result['entries']:
            assert entry['read'] is False
        if make_empty:
            entry_generators.clear()
        r = client.get(result['next_url'])
        result = json.loads(r.data)
        for entry in result['entries']:
            assert entry['read'] is False


@mark.parametrize('make_empty', [True, False])
def test_request_same_feed(make_empty, xmls_for_next):
    with app.test_client() as client:
        r1 = client.get('/-categoryone/feeds/' +
                        get_hash('http://feedone.com/') +
                        '/entries/')
        r2 = client.get('/-categoryone/feeds/' +
                        get_hash('http://feedone.com/') +
                        '/entries/')
        r1_result = json.loads(r1.data)
        r2_result = json.loads(r2.data)
        r1_next = client.get(r1_result['next_url'])
        if make_empty:
            entry_generators.clear()
        r2_next = client.get(r2_result['next_url'])
        r1_result = json.loads(r1_next.data)
        r2_result = json.loads(r2_next.data)
        assert r1_result['entries'] == r2_result['entries']
