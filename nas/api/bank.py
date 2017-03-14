# -*- coding: utf-8 -*-

from flask import Blueprint, make_response, json, current_app
from webargs.flaskparser import use_args
from marshmallow import validates, ValidationError

from ..utils import RestBlueprint, update_model
from ..models import Bank, db
from . import ModelSchema

bank_api = RestBlueprint('api.bank', __name__)


class BankSchema(ModelSchema):

    class Meta:
        model = Bank


@bank_api.route('')
def list():
    q = Bank.query.all()
    return BankSchema(many=True).dump(q).data, 200, {'X-Total-Count': len(q)}


@bank_api.route('', methods=['POST'])
@use_args(BankSchema(strict=True, partial=True))
def create(properties):
    if 'name' not in properties:
        raise ValueError("'name' field must be present")
    bank = Bank(**properties)
    db.session.add(bank)
    db.session.commit()
    return BankSchema().dump(bank).data, 201


@bank_api.route('/<int:id>', methods=['GET'])
def get(id):
    b = Bank.query.get_or_404(id)
    return BankSchema().dump(b).data


@bank_api.route('/<int:id>', methods=['PATCH'])
@use_args(BankSchema(strict=True, partial=True))
def update(properties, id):
    bank = Bank.query.get_or_404(id)
    update_model(bank, properties)
    db.session.commit()
    return BankSchema().dump(bank).data


@bank_api.route('/<int:id>', methods=['DELETE'])
def delete(id):
    b = Bank.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return '', 204
