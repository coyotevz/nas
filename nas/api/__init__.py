# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify


URL_PREFIX = '/api'

api = Blueprint('api', __name__)

@api.route('')
def index():
    return jsonify({
        'message': "This is api root for Nobix Application Server REST API v1",
    })


def configure_api(app):
    app.register_blueprint(api, url_prefix=URL_PREFIX)
    app.register_blueprint(bank_api, url_prefix=URL_PREFIX + '/banks')
    app.register_blueprint(bank_account_api, url_prefix=URL_PREFIX + '/bank_accounts')


from .bank import bank_api
from .bank_account import bank_account_api
