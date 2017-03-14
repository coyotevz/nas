# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from flask_marshmallow import Marshmallow
URL_PREFIX = '/api'

ma = Marshmallow()

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
    app.register_blueprint(bank_account_api, url_prefix=URL_PREFIX + '/bank_accounts')


class ModelSchema(ma.ModelSchema):

    def make_instance(self, data):
        return data


from .bank import bank_api
from .bank_account import bank_account_api
