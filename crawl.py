import hashlib
import os

from libearth.crawler import crawl
from libearth.feedlist import FeedList
from libearth.schema import write

REPOSITORY = 'repo'
OPML = 'earthreader.opml'

if not os.path.isdir(REPOSITORY):
    os.mkdir(REPOSITORY)

try:
    feedlist = FeedList(os.path.join(REPOSITORY, OPML))
    urllist = [feed.xml_url for feed in feedlist.get_all_feeds()]
except IOError as e:
    pass

generator = crawl(urllist, 2)

for feed_url, (feed_data, crawler_hints) in generator:
    file_name = hashlib.sha1(feed_url).hexdigest()
    with open(os.path.join('repo', file_name + '.xml'), 'w') as f:
        for chunk in write(feed_data, indent='    ', canonical_order=True):
            f.write(chunk)
