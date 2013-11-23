.. image:: https://raw.github.com/earthreader/web/master/artwork/icon_256x256.png


Earth Reader for Web
====================

Web frontend of Earth Reader.

Distributed under `AGPLv3`__ or later.

__ http://www.gnu.org/licenses/agpl-3.0.html


Install
-------

You can install Earth Reader for Web using ``pip``:

.. code-block:: console

   $ pip install git+git://github.com/earthreader/web.git

Then you can use command ``earthreader``.

.. code-block:: console

   $ earthreader -h


Usage
-----

Crawl
~~~~~

.. code-block:: console

   $ earthreader crawl <repository dir>

Server
~~~~~~

``<repository dir>`` is a directory where all data are stored.

.. code-block:: console

   $ earthreader server <repository dir>
   $ #with port
   $ earthreader server -p <port> <repository dir>
   $ #with debug mode
   $ earthreader server -d <repository dir>

And open ``http://localhost:<port>/`` with your browser.

WSGI
++++

You can attach Earth Reader to Apache with `mod_wsgi`_ like this:

.. code-block:: apache

   <VirtualHost *:80>
     ServerName yourwebsite.com
     WSGIDaemonProcess earthreader user=www-data group=www-data threads=1
     WSGIScriptAlias / /var/wsgi/earthreader.wsgi

     <Directory /var/wsgi/>
        WSGIProcessGroup earthreader
        WSGIApplicationGroup %{GLOBAL}

        Order deny,allow
        Allow from all
        <!-- For security, We prefer use auth system. -->
        AuthType Basic
        AuthName "Private rss reader"
        AuthUserFile /var/wsgi/earthreader.htpasswd
        Require valid-user
     </Directory>
   </VirtualHost>

.. code-block:: python

   #!/usr/bin/env python
   #/var/wsgi/earthreader.wsgi
   import sys
   sys.path.insert(0, '<Directory where earthreader installed>')

   from earthreader.web import app as application
   application.config.update(dict(
       REPOSITORY='<repository dir>'
       ))

And open ``http://yourwebsite.com/`` in your browser.

.. _mod_wsgi: http://code.google.com/p/modwsgi/


Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

Vim-inspired keyboard shortcuts are also available:

- ``j``/``k``: Go to older/newer entry.
- ``n``/``p``: Down/Up with feed list.
- ``o``: Open entry in new tab.
- ``r``: Refresh current feed.
- ``s``: Star/Unstar.
- ``u``: Mark as unread.
- ``?``: This help message.


Links
-----

Earth Reader
   http://earthreader.org/

libearth
   http://github.com/earthreader/libearth/

Git repository (GitHub)
   http://github.com/earthreader/web/

Issue tracker (GitHub)
   http://github.com/earthreader/web/issues

Continuous integration (Travis)
   http://travis-ci.org/earthreader/web

   .. image:: https://travis-ci.org/earthreader/web.png?branch=master
      :alt: Build Status
      :target: https://travis-ci.org/earthreader/web
