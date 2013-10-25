Earth Reader for Web
====================

Web frontend of Earth Reader.

Distributed under `AGPLv3`__ or later.

__ http://www.gnu.org/licenses/agpl-3.0.html


Install
-------

You can install earthreader by pip

    $ pip install earthreader

Then you can use command 'earthreader'

    $ earthreader -h


Usage
-----

Crawl
~~~~~

.. code-block:: console

   $ earthreader crawl <repository dir>

Server
~~~~~~

.. code-block:: console

   $ earthreader server <repository dir>
   $ #with port
   $ earthreader server -p <port> <repository dir>
   $ #with debug mode
   $ earthreader server -d <repository dir>

**<repository dir>** is a directory where feeds saved.
