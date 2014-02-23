import contextlib
try:
    import urllib2
except ImportError:
    from urllib import request as urllib2

from earthreader.web.app import app


# See also http://wiki.whatwg.org/wiki/Validator.nu_Web_Service_Interface
VALIDATOR_URL = 'http://validator.nu/?out=text'

with app.test_client() as client:
    response = client.get('/')
    content_type = response.headers['content-type']
    body = response.data

request = urllib2.Request(
    VALIDATOR_URL,
    data=body,
    headers={'Content-Type': content_type}
)

with contextlib.closing(urllib2.urlopen(request)) as response:
    message = response.read()
    failed = message.rstrip().endswith('There were errors.')
    print(message)
    raise SystemExit(int(failed))
