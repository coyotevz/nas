# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from ..tonic import Api

from .bank import BankResource, BankAccountResource
from .supplier import SupplierResource

URL_PREFIX = ''

def configure_api(app):
    api = Api(app, prefix=URL_PREFIX)

    api.register_resource(BankResource)
    api.register_resource(BankAccountResource)
    api.register_resource(SupplierResource)
