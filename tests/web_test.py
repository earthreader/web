from flask import json

from earthreader.web import app


def test_entries():
    with app.test_client() as client:
        # 404 Not Found
        r = client.get('/feeds/does-not-exist/')
        assert r.status_code == 404
        # 200 OK
        r = client.get('/feeds/370cabf0a39c5713b635af5830d33d1d66f0038f/')
        assert r.status_code == 200
        result = json.loads(r.data)
        assert len(result['entries']) == 20
