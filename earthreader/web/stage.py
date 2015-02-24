""":mod:`earthreader.web.stage` --- Stage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :data:`stage` in view functions.

"""
import os
import uuid

from flask import current_app, request
from six.moves import urllib
from werkzeug.local import LocalProxy

from libearth.repository import FileSystemRepository, from_url
from libearth.session import Session
from libearth.stage import Stage


def get_stage():
    try:
        return current_app.config['STAGE']
    except KeyError:
        session_id = current_app.config['SESSION_ID']
        if request.environ['wsgi.multiprocess']:
            # Stage doesn't offer safe synchronization between multiprocess.
            # Unique session identifiers are actually needed to distinguish
            # different "installations" which technically means "processes,"
            # hence we append pid to the session identifier configured by
            # the user to make them unique.
            # Note that it probably causes N times more disk usage
            # where N = the number of processes.  So we should discourage
            # using web servers of prefork/worker model in the docs.
            session_id = '{0}.{1}'.format(
                session_id or uuid.getnode(), os.getpid())
        session = Session(session_id)
        url = urllib.parse.urlparse(current_app.config['REPOSITORY'])
        if url.scheme == 'file':
            repository = FileSystemRepository(
                url.path,
                atomic=request.environ['wsgi.multithread']
            )
        else:
            repository = from_url(current_app.config['REPOSITORY'])
        stage = Stage(session, repository)
        current_app.config['STAGE'] = stage
        return stage


#: (:class:`~werkzeug.local.LocalProxy` of :class:`~libearth.stage.Stage`)
#: The context local stage. Use this.
stage = LocalProxy(get_stage)
