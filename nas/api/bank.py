# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from marshmallow_sqlalchemy import ModelSchema

from ..models import Bank


class RestBlueprint(Blueprint):

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__)

            def new_f(*args, **kwargs):
                return jsonify(f(*args, **kwargs))

            self.add_url_rule(rule, endpoint, new_f, **options)

            return new_f
        return decorator


bank_api = RestBlueprint('api.bank', __name__)


class BankSchema(ModelSchema):

    class Meta:
        model = Bank


@bank_api.route('')
def list():
    q = Bank.query
    return BankSchema(many=True).dump(q).data

@bank_api.route('', methods=['POST'])
def create():
    return 'bank create'

@bank_api.route('/<int:id>', methods=['GET'])
def get(id):
    return 'get bank {}'.format(id)

@bank_api.route('/<int:id>', methods=['PATCH'])
def update(id):
    return 'update bank {}'.format(id)

@bank_api.route('/<int:id>', methods=['DELETE'])
def delete(id):
    return 'delete bank {}'.format(id)
