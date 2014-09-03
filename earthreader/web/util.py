""":mod:`earthreader.web.util --- Utility functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse
import hashlib

from libearth.compat import binary


def autofix_repo_url(urlstr):
    url = urlparse.urlparse(urlstr)
    if url.scheme == '':
        return urlparse.urljoin('file://', os.path.join(os.getcwd(), urlstr))
    return urlstr


def get_hash(name):
    return hashlib.sha1(binary(name)).hexdigest()
