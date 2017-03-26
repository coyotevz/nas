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
    import pudb; pudb.set_trace
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

    # only for debug purpose
    @app.route('/urls')
    def show_urls():
        column_headers = ('Rule', 'Endpoint', 'Methods')
        order = 'rule'
        rows = [('-'*4, '-'*8, '-'*9)]  # minimal values to take
        rules = sorted(app.url_map.iter_rules(),
                    key=lambda rule: getattr(rule, order))
        for rule in rules:
            rows.append((rule.rule, rule.endpoint, ', '.join(rule.methods)))

        rule_l = len(max(rows, key=lambda r: len(r[0]))[0])
        ep_l = len(max(rows, key=lambda r: len(r[1]))[1])
        meth_l = len(max(rows, key=lambda r: len(r[2]))[2])

        str_template = '%-' + str(rule_l) + 's' + \
                    ' %-' + str(ep_l) + 's' + \
                    ' %-' + str(meth_l) + 's'
        table_width = rule_l + 2 + ep_l + 2 + meth_l

        out = (str_template % column_headers) + '\n' + '-' * table_width
        for row in rows[1:]:
            out += '\n' + str_template % row

        return out+'\n', 200, {'Content-Type': 'text/table'}
