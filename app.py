"""GUI launcher for OS X

You can build it using py2app_::

   $ pip install py2app
   $ python setup.py build_sass
   $ python setup.py py2app

.. _py2app: https://pypi.python.org/pypi/py2app/

"""
import Tkinter as tk
import os.path
import socket
import threading
import urlparse
import webbrowser

from earthreader.web.app import app, spawn_worker
from libearth.session import Session
from waitress import serve

host = '0.0.0.0'
s = socket.socket()
s.bind((host, 0))
port = s.getsockname()[1]
s.close()


def server():
    directory = os.path.expanduser('~/.earthreader')
    repository = urlparse.urljoin('file://', directory)
    session_id = Session().identifier
    app.config.update(REPOSITORY=repository, SESSION_ID=session_id)
    spawn_worker()
    serve(app, host=host, port=port)


def open_webbrowser():
    webbrowser.open('http://{}:{}'.format(host, port))


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar)
    filemenu.add_command(label="Open Browser", command=open_webbrowser)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)

    proc = threading.Thread(target=server)
    proc.daemon = True
    proc.start()
    open_webbrowser()
    root.mainloop()
