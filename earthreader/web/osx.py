""":mod:`earthreader.web.osx` --- GUI launcher for OS X
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can build it using py2app_::

   $ pip install py2app
   $ python setup.py py2app

.. _py2app: https://pypi.python.org/pypi/py2app/

"""
import os.path
import threading
import webbrowser

from six.moves import urllib, tkinter as tk
from libearth.session import Session
from waitress.server import create_server

from . import create_app


def open_webbrowser(port):
    """Opens default web browser to localhost with given port."""
    webbrowser.open('http://0.0.0.0:{}'.format(port))


def main():
    """Entrypoint for OS X."""
    root = tk.Tk()
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar)
    filemenu.add_command(label="Open Browser",
                         command=lambda: open_webbrowser(port))
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)
    root.withdraw()
    directory = os.path.expanduser('~/.earthreader')
    repository = urllib.parse.urljoin('file://', directory)
    session_id = Session().identifier
    app = create_app(REPOSITORY=repository, SESSION_ID=session_id)
    server = create_server(app, port=0)
    port = server.effective_port
    proc = threading.Thread(target=server.run)
    proc.daemon = True
    proc.start()
    open_webbrowser(port)
    root.mainloop()
