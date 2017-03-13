# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from flask_marshmallow import Marshmallow
URL_PREFIX = '/api/v1'

ma = Marshmallow()

from .bank import bank_api

api = Blueprint('api', __name__)

@api.route('')
def index():
    return jsonify({
        'message': "This is api root for Nobix Application Server REST API v1",
    })


def configure_api(app):
    ma.init_app(app)
    app.register_blueprint(api, url_prefix=URL_PREFIX)
    app.register_blueprint(bank_api, url_prefix=URL_PREFIX + '/banks')
