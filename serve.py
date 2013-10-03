import optparse
import socket

from earthreader.web import app


parser = optparse.OptionParser()
parser.add_option('-H', '--host',
                  default='0.0.0.0',
                  help='Host to listen.  [%default]')
parser.add_option('-p', '--port',
                  type='int',
                  default=5000,
                  help='Port number to listen.  [%default]')
parser.add_option('-d', '--debug',
                  default=False,
                  action='store_true',
                  help='Debug mode.  It makes the server possible to '
                       'automatically restart when files touched.')

options, args = parser.parse_args()
try:
    app.run(host=options.host, port=options.port, debug=options.debug)
except socket.error as e:
    parser.error(str(e))
