import glob
import hashlib
import os
import os.path
import shutil
import traceback

from flask import json

from libearth.compat import binary
from libearth.crawler import crawl
from libearth.feedlist import FeedList, Feed
from libearth.schema import write

from earthreader.web import app

import httpretty
from pytest import yield_fixture


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
    xmlUrl="http://feedthree.com/atom/" />
    <outline text="categorythree" title="categorythree">
        <outline type="atom" text="Feed Four" title="Feed Four"
        xmlUrl="http://feedfour.com/feed/atom/" />
    </outline>
  </body>
</opml>
'''


feed_one= '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed One</title>
    <id>http://feedone.com/feed/atom/</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
</feed>
'''

feed_two= '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Two</title>
    <id>http://feedtwo.com/feed/atom/</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
</feed>
'''


feed_three= '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Three</title>
    <id>http://feedthree.com/feed/atom/</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
</feed>
'''


feed_four = '''
<feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">Feed Four</title>
    <id>http://feedfour.com/feed/atom/</id>
    <updated>2013-08-19T07:49:20+07:00</updated>
</feed>
'''


@yield_fixture
def xmls():
    os.mkdir(REPOSITORY)
    feed_list = FeedList(opml, is_xml_string=True)
    feed_list.save_file(REPOSITORY + OPML)
    yield
    shutil.rmtree(REPOSITORY)
    

def test_all_feeds(xmls):
    with app.test_client() as client:
        r = client.get('/feeds/')
        assert r.status_code == 200
        result = json.loads(r.data)
        feeds = result['feeds']
        assert feeds[0]['title'] == 'Feed Three'
        assert feeds[1]['title'] == 'categoryone'
        assert feeds[1]['feeds'][0]['title'] == 'Feed One'
        assert feeds[1]['feeds'][1]['title'] == 'categorytwo'
        assert feeds[1]['feeds'][1]['feeds'][0]['title'] == 'Feed Two'
        assert feeds[2]['title'] == 'categorythree'
        assert feeds[2]['feeds'][0]['title'] == 'Feed Four'
