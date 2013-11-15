Earth Reader for Web
====================

Web frontend of Earth Reader.

Distributed under `AGPLv3`__ or later.

__ http://www.gnu.org/licenses/agpl-3.0.html


Install
-------

You can install earthreader by pip.

.. code-block:: console

   $ pip install earthreader

Then you can use command 'earthreader'.

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

**<repository dir>** is a directory where feeds saved.

.. code-block:: console

   $ earthreader server <repository dir>
   $ #with port
   $ earthreader server -p <port> <repository dir>
   $ #with debug mode
   $ earthreader server -d <repository dir>

And open **http://localhost:<port>/** with your browser.

WSGI
++++

You can attach earthreader to apache with `mod_wsgi`__ like this:

.. code-block:: apache

   WSGIDaemonProcess earthreader user=www-data group=www-data threads=1
   WSGIScriptAlias /earthreader /var/wsgi/earthreader.wsgi
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

.. code-block:: python

   #!/usr/bin/env python
   #/var/wsgi/earthreader.wsgi
   import sys
   sys.path.insert(0, '<Directory where earthreader installed>')

   from earthreader.web import app as application
   application.config.update(dict(
       REPOSITORY='<repository dir>'
       ))

And open **http://your.website.domain/earthreader/** with your browser.

__ http://flask.pocoo.org/docs/deploying/mod_wsgi/


Shortcuts
=========

Vim-like keyboard shortcuts are available in earthreader web

- j/k : Go to older/newer entry
- o : open entry in new tab
- u : mark as unread
- s : star/unstar


Links
=====

earthreader
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
