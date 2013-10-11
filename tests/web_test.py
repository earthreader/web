try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import glob
import hashlib
import os
import os.path
import re
import traceback
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from flask import json, url_for

from libearth.compat import binary
from libearth.crawler import crawl
from libearth.feedlist import (Feed as FeedOutline,
                               FeedCategory as CategoryOutline, FeedList)
from libearth.schema import write

from earthreader.web import app, POST_FEED, POST_CATEGORY

from pytest import fixture


@app.errorhandler(400)
def bad_request_handler_for_testing(exception):
    '''Custom error handler of :http:statuscode:`400` for unit testing
    to know how it's going in the application.

    '''
    traceback.print_exc(exception)
    return (
        traceback.format_exc(exception),
        400,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


@app.errorhandler(500)
def server_error_handler_for_testing(exception):
    '''Custom error handler of :http:statuscode:`500` for unit testing
    to know how it's going in the application.

    '''
    traceback.print_exc(exception)
    return (
        traceback.format_exc(exception),
        500,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


app.config.update(dict(
    REPOSITORY='tests/repo/',
    OPML='test.opml'
))


REPOSITORY = app.config['REPOSITORY']
OPML = app.config['OPML']


opml = '''
<opml version="1.0">
  <head>
    <title>test opml</title>
  </head>
  <body>
    <outline text="categoryone" title="categoryone">
        <outline type="atom" text="Feed One" title="Feed One"
        xmlUrl="http://feedone.com/feed/atom/" />
        <outline text="categorytwo" title="categorytwo">
            <outline type="atom" text="Feed Two" title="Feed Two"
            xmlUrl="http://feedtwo.com/feed/atom/" />
        </outline>
    </outline>
    <outline type="atom" text="Feed Three" title="Feed Three"
    xmlUrl="http://feedthree.com/feed/atom/" />
    <outline text="categorythree" title="categorythree">
        <outline type="atom" text="Feed Four" title="Feed Four"
        xmlUrl="http://feedfour.com/feed/atom/" />
    </outline>
  </body>
</opml>
'''


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
        if isinstance(child, FeedOutline):
            urls.append(child.xml_url)
        elif isinstance(child, CategoryOutline):
            get_feed_urls(child, urls)
    return urls


def mock_response(req):
    if req.get_full_url() == 'http://feedone.com/feed/atom/':
        resp = urllib2.addinfourl(StringIO(feed_one), 'mock message',
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp
    if req.get_full_url() == 'http://feedtwo.com/feed/atom/':
        resp = urllib2.addinfourl(StringIO(feed_two), 'mock message',
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp
    if req.get_full_url() == 'http://feedthree.com/feed/atom/':
        resp = urllib2.addinfourl(StringIO(feed_three), 'mock message',
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp
    if req.get_full_url() == 'http://feedfour.com/feed/atom/':
        resp = urllib2.addinfourl(StringIO(feed_four), 'mock message',
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp
    if req.get_full_url() == 'http://feedfive.com/feed/atom/':
        resp = urllib2.addinfourl(StringIO(feed_to_add), 'mock message',
                                  req.get_full_url())
        resp.code = 200
        resp.msg = "OK"
        return resp


class TestHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        return mock_response(req)


my_opener = urllib2.build_opener(TestHTTPHandler)
urllib2.install_opener(my_opener)


@fixture
def xmls(request):
    if not os.path.isdir(REPOSITORY):
        os.mkdir(REPOSITORY)
    feed_list = FeedList(opml, is_xml_string=True)
    feed_urls = get_feed_urls(feed_list)
    generator = crawl(feed_urls, 4)
    for result in generator:
        feed_data = result[1][0]
        feed_url = result[0]
        file_name = hashlib.sha1(binary(feed_url)).hexdigest() + '.xml'
        with open(REPOSITORY + file_name, 'w+') as f:
            for chunk in write(feed_data, indent='    ',
                               canonical_order=True):
                f.write(chunk)
    feed_list.save_file(REPOSITORY + OPML)

    def remove_test_repo():
        files = glob.glob(REPOSITORY + '*')
        for file in files:
            os.remove(file)
        os.rmdir(REPOSITORY)

    request.addfinalizer(remove_test_repo)


def test_all_feeds(xmls):
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        feeds = result['feeds']
        assert feeds[0]['title'] == 'categoryone'
        assert feeds[0]['feeds'][0]['title'] == 'Feed One'
        assert feeds[0]['feeds'][1]['title'] == 'categorytwo'
        assert feeds[0]['feeds'][1]['feeds'][0]['title'] == 'Feed Two'
        assert feeds[1]['title'] == 'Feed Three'
        assert feeds[2]['title'] == 'categorythree'
        assert feeds[2]['feeds'][0]['title'] == 'Feed Four'


def test_feed_entries(xmls):
    FEED_ID_PATTERN = re.compile('(?:.?)+/feeds/(.+)/entries/')
    ENTRY_ID_PATTERN = re.compile('(?:.?)+/feeds/(?:.+)/entries/(.+)/')
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        feeds = result['feeds']
        # Feed Three
        feed_url = feeds[1]['feed_url']
        r1 = client.get(feed_url)
        assert r1.status_code == 200
        r1_data = json.loads(r1.data)
        assert r1_data['title'] == 'Feed Three'
        entry_url = r1_data['entries'][0]['entry_url']
        entry_r1 = client.get(entry_url)
        entry_r1_data = json.loads(entry_r1.data)
        assert entry_r1_data['content'] == \
            'This is content of Entry One in Feed Three'
        assert entry_r1_data['updated'] == \
            '2013-08-21 07:49:20+07:00'
        # Feed One
        feed_url = feeds[0]['feeds'][0]['feed_url']
        r1 = client.get(feed_url)
        assert r1.status_code == 200
        r1_data = json.loads(r1.data)
        match = FEED_ID_PATTERN.match(feed_url)
        feed_id = match.group(1)
        r2 = client.get('/feeds/' + feed_id + '/entries/')
        assert r2.status_code == 200
        r2_data = json.loads(r2.data)
        assert r1_data['title'] == r2_data['title'] == 'Feed One'
        entry_url = r1_data['entries'][0]['entry_url']
        entry_r1 = client.get(entry_url)
        entry_r1_data = json.loads(entry_r1.data)
        entry_id = ENTRY_ID_PATTERN.match(entry_url).group(1)
        entry_r2 = client.get('/feeds/' + feed_id + '/entries/' +
                              entry_id + '/')
        entry_r2_data = json.loads(entry_r2.data)
        assert entry_r1_data['content'] == entry_r2_data['content'] == \
            'This is content of Entry One in Feed One'
        assert entry_r1_data['updated'] == entry_r2_data['updated'] == \
            '2013-08-19 07:49:20+07:00'
        # Feed Two
        feed_url = feeds[0]['feeds'][1]['feeds'][0]['feed_url']
        r1 = client.get(feed_url)
        assert r1.status_code == 200
        r1_data = json.loads(r1.data)
        match = FEED_ID_PATTERN.match(feed_url)
        feed_id = match.group(1)
        r2 = client.get('/feeds/' + feed_id + '/entries/')
        assert r2.status_code == 200
        r2_data = json.loads(r2.data)
        assert r1_data['title'] == r2_data['title'] == 'Feed Two'
        entry_url = r1_data['entries'][0]['entry_url']
        entry_r1 = client.get(entry_url)
        entry_r1_data = json.loads(entry_r1.data)
        entry_id = ENTRY_ID_PATTERN.match(entry_url).group(1)
        entry_r2 = client.get('/feeds/' + feed_id + '/entries/' +
                              entry_id + '/')
        entry_r2_data = json.loads(entry_r2.data)
        assert entry_r1_data['content'] == entry_r2_data['content'] == \
            'This is content of Entry One in Feed Two'
        assert entry_r1_data['updated'] == entry_r2_data['updated'] == \
            '2013-08-20 07:49:20+07:00'
        # Feed Four
        feed_url = feeds[2]['feeds'][0]['feed_url']
        r1 = client.get(feed_url)
        assert r1.status_code == 200
        r1_data = json.loads(r1.data)
        match = FEED_ID_PATTERN.match(feed_url)
        feed_id = match.group(1)
        r2 = client.get('/feeds/' + feed_id + '/entries/')
        assert r2.status_code == 200
        r2_data = json.loads(r2.data)
        assert r1_data['title'] == r2_data['title'] == 'Feed Four'
        entry_url = r1_data['entries'][0]['entry_url']
        entry_r1 = client.get(entry_url)
        entry_r1_data = json.loads(entry_r1.data)
        entry_id = ENTRY_ID_PATTERN.match(entry_url).group(1)
        entry_r2 = client.get('/feeds/' + feed_id + '/entries/' +
                              entry_id + '/')
        entry_r2_data = json.loads(entry_r2.data)
        assert entry_r1_data['content'] == entry_r2_data['content'] == \
            'This is content of Entry One in Feed Four'
        assert entry_r1_data['updated'] == entry_r2_data['updated'] == \
            '2013-08-22 07:49:20+07:00'


def test_category_path(xmls):
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        categoryone = result['feeds'][0]
        assert categoryone['title'] == 'categoryone'
        assert categoryone['feed_url'] == \
            url_for(
                'category_all_entries',
                category_id='categoryone',
                _external=True)
        r_categoryone = client.get(categoryone['feed_url'])
        assert r_categoryone.status_code == 200
        categorytwo = result['feeds'][0]['feeds'][1]
        assert categorytwo['title'] == 'categorytwo'
        assert categorytwo['feed_url'] == \
            url_for(
                'category_all_entries',
                category_id='categoryone/categorytwo',
                _external=True)
        r_categorytwo = client.get(categorytwo['feed_url'])
        assert r_categorytwo.status_code == 200


def test_category_feeds(xmls):
    with app.test_client() as client:
        # categoryone
        r = client.get('/categoryone/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'Feed One'
        # categorytwo
        url = result['feeds'][1]['feed_url']
        r = client.get(url)
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['entries'][0]['title'] == 'Feed Two: Entry One'


def test_invalid_path(xmls):
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://feedone.com/feed/atom/')).hexdigest()
        r = client.get('/non-exist-category/feeds/' + feed_id + '/entries/')
        result = json.loads(r.data)
        assert r.status_code == 404
        assert result['error'] == 'category-path-invalid'


def test_add_feed(xmls):
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(type=POST_FEED,
                                  url='http://feedfive.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][3]['title'] == 'Feed Five'
        opml = FeedList(REPOSITORY + OPML)
        assert opml[3].title == 'Feed Five'


def test_add_feed_in_category(xmls):
    with app.test_client() as client:
        r = client.post('/categoryone/categorytwo/feeds/',
                        data=dict(type=POST_FEED,
                                  url='http://feedfive.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'Feed Two'
        assert result['feeds'][1]['title'] == 'Feed Five'
        opml = FeedList(REPOSITORY + OPML)
        assert opml[0][1][1].title == 'Feed Five'


def test_add_category(xmls):
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(type=POST_CATEGORY,
                                  title='addedcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][3]['title'] == 'addedcategory'
        opml = FeedList(REPOSITORY + OPML)
        assert opml[3].text == 'addedcategory'


def test_add_category_in_category(xmls):
    with app.test_client() as client:
        r = client.post('/categoryone/feeds/',
                        data=dict(type=POST_CATEGORY,
                                  title='addedcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][2]['title'] == 'addedcategory'
        opml = FeedList(REPOSITORY + OPML)
        assert opml[0][2].text == 'addedcategory'


def test_add_category_without_opml():
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(type=POST_CATEGORY,
                                  title='testcategory'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'testcategory'
        REPOSITORY = app.config['REPOSITORY']
        OPML = app.config['OPML']
        feed_list = FeedList(REPOSITORY + OPML)
        assert feed_list[0].text == 'testcategory'
        os.remove(REPOSITORY + OPML)
        os.rmdir(REPOSITORY)


def test_add_feed_without_opml():
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(type=POST_FEED,
                                  url='http://feedone.com/feed/atom/'))
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['feeds'][0]['title'] == 'Feed One'
        REPOSITORY = app.config['REPOSITORY']
        OPML = app.config['OPML']
        feed_list = FeedList(REPOSITORY + OPML)
        assert feed_list[0].title == 'Feed One'
    files = glob.glob(REPOSITORY + '*')
    for file in files:
        os.remove(file)
    os.rmdir(REPOSITORY)


def test_delete_feed(xmls):
    REPOSITORY = app.config['REPOSITORY']
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://feedthree.com/feed/atom/')).hexdigest()
        r = client.delete('/feeds/' + feed_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        for child in result['feeds']:
            assert child['title'] != 'Feed Three'
        assert not REPOSITORY + feed_id + '.xml' in glob.glob(REPOSITORY + '*')


def test_delete_feed_in_category(xmls):
    REPOSITORY = app.config['REPOSITORY']
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://feedtwo.com/feed/atom/')).hexdigest()
        r = client.delete('/categoryone/categorytwo/feeds/' + feed_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['feeds']) == 0
        assert not REPOSITORY + feed_id + '.xml' in glob.glob(REPOSITORY + '*')


def test_delete_feed_in_two_category(xmls):
    REPOSITORY = app.config['REPOSITORY']
    with app.test_client() as client:
        r = client.post('/feeds/',
                        data=dict(type=POST_FEED,
                                  url='http://feedone.com/feed/atom/'))
        assert r.status_code == 200
        feed_list = FeedList(REPOSITORY + OPML)
        assert feed_list[0][0].title == 'Feed One'
        assert feed_list[3].title == 'Feed One'
        feed_id = hashlib.sha1(
            binary('http://feedone.com/feed/atom/')).hexdigest()
        r = client.delete('/categoryone/feeds/' + feed_id + '/')
        assert r.status_code == 200
        feed_list = FeedList(REPOSITORY + OPML)
        for child in feed_list[0]:
            assert not child.title == 'Feed One'
        assert feed_list[3].title == 'Feed One'
        assert REPOSITORY + feed_id + '.xml' in glob.glob(REPOSITORY + '*')


def test_delete_non_exists_feed(xmls):
    with app.test_client() as client:
        r = client.delete('/feeds/non-exists-feed/')
        assert r.status_code == 400
        result = json.loads(r.data)
        assert result['error'] == 'feed-not-found-in-path'


def test_delete_category_in_root(xmls):
    with app.test_client() as client:
        r = client.delete('/categoryone/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result == json.loads(client.get('/feeds/').data)
        for child in result['feeds']:
            assert not child['title'] == 'categoryone'


def test_delete_category_in_category(xmls):
    with app.test_client() as client:
        r = client.delete('/categoryone/categorytwo/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result == json.loads(client.get('/categoryone/feeds/').data)
        for child in result['feeds']:
            assert not child['title'] == 'categorytwo'


def test_category_all_entries(xmls):
    with app.test_client() as client:
        r = client.get('/categoryone/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 2
        r = client.get('/categoryone/categorytwo/entries/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 1
