""":mod:`earthreader.web.exceptions` --- Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class IteratorNotFound(ValueError):
    """Raised when the iterator does not exist"""


class JsonException(HTTPException):
    """Base exception to return json response when raised.
    Exceptions inherit this class must declare `error`, `message`,
    and `status_code`.

    """
    def get_response(self, environ=None):
        r = jsonify(error=self.error, message=self.message)
        r.status_code = self.status_code
        return r


class InvalidCategoryID(ValueError, JsonException):
    """Raised when the category ID is not valid."""

    error = 'category-id-invalid'
    message = 'Given category id is not valid'
    status_code = 404


class FeedNotFound(ValueError, JsonException):
    """Raised when the feed is not reachable."""

    error = 'feed-not-found'
    message = 'The feed you request does not exsist'
    status_code = 404


class EntryNotFound(ValueError, JsonException):
    """Raised when the entry is not reachable."""

    error = 'entry-not-found'
    message = 'The entry you request does not exist'
    status_code = 404


class WorkerNotRunning(ValueError, JsonException):
    """Raised when the worker thread is not running."""

    error = 'worker-not-running'
    message = 'The worker thread that crawl feeds in background is not' \
              'running.'
    status_code = 404


class DocumentNotFound(ValueError, JsonException):
    """Raised when the document is not reachable"""

    error = 'unreachable-url',
    message = 'Cannot connect to given url'
    status_code = 404


class AutodiscoveryFailed(ValueError, JsonException):
    """Raised when a feed url is not found"""

    error = 'unreachable-feed-url',
    message = 'Cannot find feed url'
    status_code = 404


class FeedNotFoundInCategory(ValueError, JsonException):
    """Raised whan the feed does not exist in category"""

    error = 'feed-not-found-in-path',
    message = 'Given feed does not exist in the path'
    status_code = 400
