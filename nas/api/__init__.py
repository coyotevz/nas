# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from ..tonic import Api

from .bank import BankResource, BankAccountResource

URL_PREFIX = ''

def configure_api(app):
    api = Api(app, prefix=URL_PREFIX)

    api.register_resource(BankResource)
    api.register_resource(BankAccountResource)
