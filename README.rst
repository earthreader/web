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

If the path that doesn't exist yet is passed to CLI repository path argument or
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
The WSGI endpoint is ``earthreader.web:app``.  Note that you can provide
the path of repository by setting ``EARTHREADER_REPOSITORY`` environment
variable.

Note that you should manually invoke ``earthreader crawl`` command when
you run it using your preferred WSGI server while the standalone server
(``earthreader server`` command) automatically does it for you.  We recommend
you to register ``earthreader crawl`` command to your ``crontab``.

For example, you can run it on Gunicorn:

.. code-block:: console

   $ export EARTHREADER_REPOSITORY=/path/to/repository/dir
   $ gunicorn earthreader.web:app

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
   from earthreader.web import app as application

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

Mailing list
   earthreader@librelist.com

List archive
   http://librelist.com/browser/earthreader/

Continuous integration (Travis)
   https://travis-ci.org/earthreader/web

   .. image:: https://travis-ci.org/earthreader/web.png?branch=master
      :alt: Build Status
      :target: https://travis-ci.org/earthreader/web


Demo
----

You can try Earth Reader web here:
http://try.earthreader.org/


Changelog
---------

Version 0.3.0
~~~~~~~~~~~~~

To be released.

- Run crawler thread by default.
- Error code ``circular-refernce``, which is a typo, was renamed to
  ``circular-reference``.
- Fixed auto scroll when entry has images.
- Fixed a bug that raises ``BuildError``.  [`#49`__]
- Became to need libearth 0.3.1 or later.
- "Go to top" button on bottom.

__ https://github.com/earthreader/web/issues/49


Version 0.2.1
~~~~~~~~~~~~~

Released on July 16, 2014.

- Relative directory path on WSGI app.  [`#42`__]
- Give correct permalink.  [`#43`__]
- Workaround libearth 0.3.0 incompatibility.
- Entry list is cached by browser using ``Last-Modified`` and
  ``If-Modified-Since`` headers.

__ https://github.com/earthreader/web/issues/42
__ https://github.com/earthreader/web/issues/43


Version 0.2.0
~~~~~~~~~~~~~

Released on April 22, 2014.

- ``earthreader crawl`` command adds new options:

  - ``-f``/``--feed-id`` crawls only the specified feed if present.
  - ``-v``/``--verbose`` shows more detail information.

- Categories are folded at first.
- Keyboard shortcut for toggle folding category.
- Expand categories when click feed for mobile layout.
- Google reader style shortcuts.
- Mark all as read function. [`#28`__]
- Fixed a bug that "crawl now" button didn't work.
- Relative directory path on command line.  [`#36`__]
- GUI launcher for OS X. [`#38`__]

__ https://github.com/earthreader/web/issues/28
__ https://github.com/earthreader/web/issues/36
__ https://github.com/earthreader/web/issues/38


Version 0.1.1
~~~~~~~~~~~~~

Released on January 10, 2014.

- Fixed ``ImportError`` when ``earthreader`` command is invoked on Python 3.
  [`#25`__ by Yong Choi]
- The repository path argument format became consistent both for
  ``earthreader server`` and ``earthreader crawl`` commands.
  [`#24`__]
- Close help overlay on ``escape`` key.
  [`#27`__]
- Added ``--P``/``--profile``/``--linesman`` option, available only when
  linesman_ is installed, to ``earthreader server`` comand.
- Continue crawling when some feed raises error.
- Fix crawling bug.
- Print error when failed to remove feed.
- Fixed some Unicode coding bugs on server side.
- ``-v``/``--verbose`` option prints detailed tracebacks of
  crawler errors.
- Spinner UI while loading contents.

__ https://github.com/earthreader/web/pull/25
__ https://github.com/earthreader/web/issues/24
__ https://github.com/earthreader/web/issues/27
.. _linesman: https://pypi.python.org/pypi/linesman


Version 0.1.0
~~~~~~~~~~~~~

Released on December 23, 2013.  Alpha version.
