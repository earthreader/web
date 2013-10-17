""":mod:`earthreader.web.wsgi` --- WSGI middlewares
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re

__all__ = 'MethodRewriteMiddleware',


class MethodRewriteMiddleware(object):
    """The WSGI middleware that overrides HTTP methods for old browsers.
    HTML4 and XHTML only specify ``POST`` and ``GET`` as HTTP methods that
    ``<form>`` elements can use.  HTTP itself however supports a wider
    range of methods, and it makes sense to support them on the server.

    If you however want to make a form submission with ``PUT`` for instance,
    and you are using a client that does not support it, you can override it
    by using this middleware and appending ``?_method=PUT`` to the
    ``<form>`` ``action``.

    .. sourcecode:: html

       <form action="?_method=PUT" method="post">
         ...
       </form>

    :param app: WSGI application to wrap
    :type app: :class:`collections.Callable`
    :param input_name: the field name of the query to be aware of
    :type input_name: :class:`basestring`

    .. seealso::

       `Overriding HTTP Methods for old browsers`__ --- Flask Snippets
          A snippet written by Armin Ronacher.

    __ http://flask.pocoo.org/snippets/38/

    """

    #: (:class:`collections.Set`) The set of allowed HTTP methods.
    ALLOWED_METHODS = frozenset(['HEAD', 'GET', 'POST', 'PUT', 'DELETE'])

    #: (:class:`re.RegexObject`) The query pattern.
    PATTERN = re.compile(
        r'(?:^|&)_method=(' + '|'.join(re.escape(m) for m in ALLOWED_METHODS) +
        r')(?:&|$)'
    )

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if (environ.get('REQUEST_METHOD', '').upper() == 'POST'):
            match = self.PATTERN.search(environ.get('QUERY_STRING', ''))
            if match:
                environ = dict(environ)
                environ['REQUEST_METHOD'] = match.group(1)
        return self.app(environ, start_response)
