""":mod:`earthreader.web.exceptions` --- Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class IteratorNotFound(ValueError):
    """Raised when the iterator does not exist"""


class JsonException(HTTPException):
    """Base exception to return json response when raised.
    Exceptions inherit this class must declare `error` and `message`.

    """
    def get_response(self, environ):
        r = jsonify(error=self.error, message=self.message)
        r.status_code = 404
        return r


class InvalidCategoryID(ValueError, JsonException):
    """Raised when the category ID is not valid."""

    error = 'category-id-invalid'
    message = 'Given category id is not valid'


class FeedNotFound(ValueError, JsonException):
    """Raised when the feed is not reachable."""

    error = 'feed-not-found'
    message = 'The feed you request does not exsist'


class EntryNotFound(ValueError, JsonException):
    """Raised when the entry is not reachable."""

    error = 'entry-not-found'
    message = 'The entry you request does not exist'


class WorkerNotRunning(ValueError, JsonException):
    """Raised when the worker thread is not running."""

    error = 'worker-not-running'
    message = 'The worker thread that crawl feeds in background is not' \
              'running.'
