import glob
import hashlib
import os
import os.path
import traceback

from flask import json

from libearth.compat import binary
from libearth.crawler import crawl
from libearth.feedlist import FeedList, Feed
from libearth.schema import write

from earthreader.web import app

import httpretty
from pytest import fixture


@app.errorhandler(400)
def bad_request_handler_for_testing(exception):
    """Custom error handler of :http:statuscode:`400` for unit testing
    to know how it's going in the application.

    """
    traceback.print_exc(exception)
    return (
        traceback.format_exc(exception),
        400,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


@app.errorhandler(500)
def server_error_handler_for_testing(exception):
    """Custom error handler of :http:statuscode:`500` for unit testing
    to know how it's going in the application.

    """
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

atom_xml = """
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Atom Test</title>
    <subtitle type="text">Earth Reader</subtitle>
    <id>http://vio.atomtest.com/feed/atom</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
    <link rel="alternate" type="text/html" href="http://vio.atomtest.com/" />
    <link rel="self" type="application/atom+xml"
        href="http://vio.atomtest.com/feed/atom" />
    <author>
        <name>vio</name>
        <email>vio.bo94@gmail.com</email>
    </author>
    <category term="Python" />
    <contributor>
        <name>dahlia</name>
    </contributor>
    <generator uri="http://wordpress.com/">WordPress.com</generator>
    <icon>http://vio.atomtest.com/images/icon.jpg</icon>
    <logo>http://vio.atomtest.com/images/logo.jpg</logo>
    <rights>vio company all rights reserved</rights>
    <updated>2013-08-10T15:27:04Z</updated>
    <entry>
        <id>one</id>
        <author>
            <name>vio</name>
        </author>
        <title>Title One</title>
        <link rel="self" href="http://vio.atomtest.com/?p=12345" />
        <updated>2013-08-10T15:27:04Z</updated>
        <published>2013-08-10T15:26:15Z</published>
        <category scheme="http://vio.atomtest.com" term="Category One" />
        <category scheme="http://vio.atomtest.com" term="Category Two" />
        <content>Hello World</content>
    </entry>
    <entry xml:base="http://basetest.com/">
        <id>two</id>
        <author>
            <name>kjwon</name>
        </author>
        <title>xml base test</title>
        <published>2013-08-17T03:28:11Z</published>
        <updated>2013-08-17T03:28:11Z</updated>
    </entry>
</feed>
"""


rss_xml = """
<rss version="2.0">
<channel>
    <title>Vio Blog</title>
    <link>http://vioblog.com</link>
    <description>earthreader</description>
    <copyright>Copyright2013, Vio</copyright>
    <managingEditor>vio.bo94@gmail.com</managingEditor>
    <webMaster>vio.bo94@gmail.com</webMaster>
    <pubDate>Sat, 17 Sep 2002 00:00:01 GMT</pubDate>
    <lastBuildDate>Sat, 07 Sep 2002 00:00:01 GMT</lastBuildDate>
    <category>Python</category>
    <ttl>10</ttl>
    <item>
        <title>test one</title>
        <link>http://vioblog.com/12</link>
        <description>This is the content</description>
        <author>vio.bo94@gmail.com</author>
        <enclosure url="http://vioblog.com/mp/a.mp3" type="audio/mpeg" />
        <source url="http://sourcetest.com/rss.xml">
            Source Test
        </source>
        <category>RSS</category>
        <guid>http://vioblog.com/12</guid>
        <pubDate>Sat, 07 Sep 2002 00:00:01 GMT</pubDate>
    </item>
</channel>
</rss>
"""
rss_source_xml = """
<rss version="2.0">
    <channel>
        <title>Source Test</title>
        <link>http://sourcetest.com/</link>
        <description>for source tag test</description>
        <pubDate>Sat, 17 Sep 2002 00:00:01 GMT</pubDate>
        <item>
            <title>It will not be parsed</title>
        </item>
    </channel>
</rss>
"""


@fixture
def xmls(request):
    httpretty.enable()
    if not os.path.isdir(REPOSITORY):
        os.mkdir(REPOSITORY)
    httpretty.register_uri(httpretty.GET, "http://vio.atomtest.com/feed/atom",
                           body=atom_xml)
    httpretty.register_uri(httpretty.GET, "http://rsstest.com/rss.xml",
                           body=rss_xml)
    httpretty.register_uri(httpretty.GET, "http://sourcetest.com/rss.xml",
                           body=rss_source_xml)
    feed_urls = ['http://vio.atomtest.com/feed/atom',
                 'http://rsstest.com/rss.xml']
    feed_list = FeedList()
    generator = crawl(feed_urls, 4)
    for result in generator:
        feed_data = result[1][0]
        feed_url = result[0]
        file_name = hashlib.sha1(binary(feed_url)).hexdigest() + '.xml'
        with open(REPOSITORY + file_name, 'w+') as f:
            for chunk in write(feed_data, indent='    ',
                               canonical_order=True):
                f.write(chunk)
        feed_title = feed_data.title.value
        for link in feed_data.links:
            if link.relation == 'alternate' and link.mimetype == 'text/html':
                blog_url = link.uri
        feed = Feed('atom', feed_title, feed_url, blog_url)
        feed_list.append(feed)
    feed_list.save_file(REPOSITORY + 'test.opml')

    def remove_test_repo():
        files = glob.glob(REPOSITORY + '*')
        for file in files:
            os.remove(file)
        os.rmdir(REPOSITORY)
        httpretty.disable()

    request.addfinalizer(remove_test_repo)


def test_feeds(xmls):
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        feeds = result['feeds']
        title_list = ['Atom Test', 'Vio Blog']
        assert len(feeds) == 2
        for feed in feeds:
            assert feed['title'] in title_list


added_feed = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <id>http://addedfeed.com/atom</id>
    <title>It will be added in opml and repository</title>
    <updated>2013-10-01T16:53:22Z</updated>
    <link rel="alternate" type="text/html" href="http://addedfeed.com" />
</feed>
'''


html_with_no_feed_url = '''
<html>
<head>
<body>
</body>
</head>
</html>
'''


def test_add_feed(xmls):
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, 'http://addedfeed.com/atom',
                           body=added_feed)
    httpretty.register_uri(httpretty.GET, 'http://nofeedhtml.com/',
                           body=html_with_no_feed_url)
    with app.test_client() as client:
        # 200 OK
        r = client.post('/feeds/', data=dict(url='http://addedfeed.com/atom'))
        assert r.status_code == 200
        feed_list = FeedList(REPOSITORY + OPML)
        assert len(feed_list) == 3
        assert r.data == client.get('/feeds/').data
        # 400 Bad Request: unreachable-url
        r = client.post('/feeds/', data=dict(url='not-exists-url'))
        assert r.status_code == 400
        result = json.loads(r.data)
        assert result['error'] == 'unreachable-url'
        assert result['message'] == 'Cannot connect to given url'
        # 400 Bad Request: unreachable-feed-url
        r = client.post('/feeds/', data=dict(url='http://nofeedhtml.com/'))
        assert r.status_code == 400
        result = json.loads(r.data)
        assert result['error'] == 'unreachable-feed-url'
        assert result['message'] == 'Cannot find feed url'
    httpretty.disable()


def test_delete_feed(xmls):
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://vio.atomtest.com/feed/atom')
        ).hexdigest()
        r = client.delete('/feeds/' + feed_id + '/')
        assert r.status_code == 200
        feed_list = FeedList(REPOSITORY + OPML)
        assert len(feed_list) == 1
        assert not os.path.exists(REPOSITORY + feed_id + '.xml')
        assert r.data == client.get('/feeds/').data


def test_entries(xmls):
    with app.test_client() as client:
        # 404 Not Found
        r = client.get('/feeds/does-not-exist/')
        assert r.status_code == 404
        result = json.loads(r.data)
        assert result['error'] == 'feed-not-found'
        assert result['message'] == 'Given feed does not exist'
        # 200 OK
        file_name = \
            hashlib.sha1(
                binary('http://vio.atomtest.com/feed/atom')
            ).hexdigest()
        r = client.get('/feeds/' + file_name + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result['title'] == 'Atom Test'
        assert result['entries'][0]['title'] == 'Title One'
        assert result['entries'][1]['title'] == 'xml base test'


def test_entry_content(xmls):
    with app.test_client() as client:
        feed_id = hashlib.sha1(
            binary('http://vio.atomtest.com/feed/atom')
        ).hexdigest()
        entry_id = hashlib.sha1(
            binary('http://vio.atomtest.com/feed/one')
        ).hexdigest()
        r = client.get('/feeds/' + feed_id + '/' + entry_id + '/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert result.get(u'content') == 'Hello World'
        # 404 Not Found: entry-not-found
        entry_id = 'not-exists'
        r = client.get('/feeds/' + feed_id + '/' + entry_id + '/')
        assert r.status_code == 404
        result = json.loads(r.data)
        assert result['error'] == 'entry-not-found'
        assert result['message'] == 'Given entry does not exist'
        # 404 Not Found: feed-not-found
        feed_id = 'not-exists'
        r = client.get('/feeds/' + feed_id + '/' + entry_id + '/')
        assert r.status_code == 404
        result = json.loads(r.data)
        assert result['error'] == 'feed-not-found'
        assert result['message'] == 'Given feed does not exist'
