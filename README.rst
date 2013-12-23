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

   $ pip install EarthReader-Web

Then you can use command ``earthreader``.

.. code-block:: console

   $ earthreader -h


Repository
----------

*Repository* is a directory to store data.  It can be inside of Dropbox_ or
`Google Drive`_ folder to be synchronized__ with other devices.  You also
can synchronize the repository directory using rsync_.

If the path that doesn't exist yet is passed to ``--repository`` option or
``EARTHREADER_REPOSITORY`` environment variable the new folder will be
automatically created.

.. _Dropbox: https://www.dropbox.com/
.. _Google Drive: https://drive.google.com/
__ http://blog.earthreader.org/2013/12/sync/
.. _rsync: http://rsync.samba.org/


Standalone server
-----------------

You can run Earth Reader for Web using its standalone server:

.. code-block:: console

   $ earthreader server /path/to/repository/dir
   $ earthreader server -p 8080 /path/to/repository/dir  # listen to 8080 port
   $ earthreader server -d /path/to/repository/dir  # debug mode

And then open ``http://localhost:<port>/`` with your browser.


WSGI server
-----------

Earth Reader for Web is actually an ordinary WSGI_-compliant web application,
so you can run it using your preferred WSGI server e.g. Gunicorn_, `mod_wsgi`_.
The WSGI endpoint is ``earthreader.web.app:app``.  Note that you can provide
the path of repository by setting ``EARTHREADER_REPOSITORY`` environment
variable.

For example, you can run it on Gunicorn:

.. code-block:: console

   $ export EARTHREADER_REPOSITORY=/path/to/repository/dir
   $ gunicorn earthreader.web.app:app

Or you can attach Earth Reader to Apache with mod_wsgi like this:

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
        # We recommend you to use authorization for security.
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
   from earthreader.web.app import app as application

   application.config.update(
       REPOSITORY='/path/to/repository/dir'
   )

And open ``http://yourwebsite.com/`` in your browser.

.. _WSGI: http://www.python.org/dev/peps/pep-3333/
.. _Gunicorn: http://gunicorn.org/
.. _mod_wsgi: http://code.google.com/p/modwsgi/


Crawler
-------

You can manually crawl feeds as well via CLI:

.. code-block:: console

   $ earthreader crawl /path/to/repository/dir


Keyboard shortcuts
------------------

Vim-inspired keyboard shortcuts are also available:

- ``j``/``k``: Older/newer entry.
- ``n``/``p``: Next/previous subscription.
- ``o``: Open entry in new tab.
- ``r``: Refresh the feed.
- ``s``: Star/unstar.
- ``u`` or ``m``: Mark as unread.
- ``?``: This help message.


Links
-----

Earth Reader
   http://earthreader.org/

libearth
   https://github.com/earthreader/libearth

Git repository (GitHub)
   https://github.com/earthreader/web

Issue tracker (GitHub)
   https://github.com/earthreader/web/issues

Continuous integration (Travis)
   https://travis-ci.org/earthreader/web

   .. image:: https://travis-ci.org/earthreader/web.png?branch=master
      :alt: Build Status
      :target: https://travis-ci.org/earthreader/web


Changelog
---------

Version 0.1.0
~~~~~~~~~~~~~

Released on December 23, 2013.  Alpha version.
