# -*- coding: utf-8 -*-

import locale
locale.setlocale(locale.LC_ALL, '')

from flask import Flask, request
from nas.api import configure_api
from nas.models import configure_db
from nas.utils.converters import (
    ListConverter, RangeConverter, RangeListConverter
)


DEFAULT_APPNAME = 'nobix-application-server'


def create_app(config=None, app_name=None):

    if app_name is None:
        app_name = DEFAULT_APPNAME

    app = Flask(app_name, static_folder=None)

    configure_app(app, config)
    configure_db(app)
    # configure_auth(app)
    configure_api(app)

    return app


def configure_app(app, config=None):

    if config is not None:
        app.config.from_object(config)
    else:
        try:
            app.config.from_object('localconfig.LocalConfig')
        except ImportError:
            if os.getenv('DEV') == 'yes':
                app.config.from_object('nas.config.DevelopmentConfig')
                app.logger.info("Config: Development")
            elif os.getenv('TEST') == 'yes':
                app.config.from_object('nas.config.TestConfig')
                app.logger.info("Config: Test")
            else:
                app.config.from_object('nas.config.ProductionConfig')
                app.logger.info("Config: Production")

    # Add additional converters
    app.url_map.converters['list'] = ListConverter
    app.url_map.converters['range'] = RangeConverter
    app.url_map.converters['rangelist'] = RangeListConverter

    @app.after_request
    def add_cors_headers(response):
        if 'Origin' in request.headers:

            a = response.headers.add
            a('Access-Control-Allow-Origin', request.headers['Origin'])
            a('Access-Control-Allow-Credentials', 'true')
            a('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            a('Access-Control-Allow-Methods', 'GET,PUT,PATCH,POST,DELETE')
        return response
