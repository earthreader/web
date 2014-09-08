""":mod:`earthreader.web` --- Earth Reader for Web
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Flask

from . import main
from .wsgi import MethodRewriteMiddleware


def create_app(**kwargs):
    """The application factory."""
    app = Flask(__name__)
    app.config.update(kwargs)
    app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)
    app.register_blueprint(main.bp)
    return app
