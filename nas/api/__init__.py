# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from .bank import bank_api

URL_PREFIX = '/api/v1'

api = Blueprint('api', __name__)


@api.route('')
def index():
    return jsonify({
        'message': "This is api root for Nobix Application Server REST API v1",
    })


def configure_api(app):
    app.register_blueprint(api, url_prefix=URL_PREFIX)
    app.register_blueprint(bank_api, url_prefix=URL_PREFIX + '/banks')
