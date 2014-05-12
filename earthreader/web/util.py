import os
import urlparse


def autofix_repo_url(urlstr):
    url = urlparse.urlparse(urlstr)
    if url.scheme == '':
        return urlparse.urljoin('file://', os.path.join(os.getcwd(), urlstr))
    return urlstr
