""":mod:`earthreader.web.util --- Utility functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os
import hashlib

from six.moves import urllib

from libearth.compat import binary


def autofix_repo_url(urlstr):
    url = urllib.parse.urlparse(urlstr)
    if url.scheme == '':
        return urllib.parse.urljoin('file://', os.path.join(os.getcwd(),
                                                            urlstr))
    return urlstr


def get_hash(name):
    return hashlib.sha1(binary(name)).hexdigest()
