from werkzeug.test import Client
from werkzeug.wrappers import Response

from earthreader.web.wsgi import MethodRewriteMiddleware


def test_method_rewrite_middleware():
    def test_app(environ, start_response):
        start_response(b'200 OK', [(b'Content-Type', b'text/plain')])
        return [environ['REQUEST_METHOD'].upper()]
    client = Client(MethodRewriteMiddleware(test_app), Response)
    response = client.get('/')
    assert response.data == b'GET'
    response = client.get('/?_method=PUT')
    assert response.data == b'GET'
    response = client.post('/')
    assert response.data == b'POST'
    response = client.post('/?_method=PUT')
    assert response.data == b'PUT'
    response = client.post('/?_method=DELETE')
    assert response.data == b'DELETE'
