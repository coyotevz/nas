# -*- coding: utf-8 -*-

from flask import abort
from marshmallow import Schema, fields, validates, ValidationError
from webargs.flaskparser import use_args


from ..utils import RestBlueprint, update_model
from ..models import Bank, BankAccount, db
from .bank_account import BankAccountSchema

bank_api = RestBlueprint('api.bank', __name__)


class BankSchema(Schema):

    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    bcra_code = fields.String(lenght=8)
    cuit = fields.String(length=11)


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


@bank_api.route('/<int:id>/accounts')
def list_accounts(id):
    b = Bank.query.get_or_404(id)
    return (BankAccountSchema(many=True).dump(b.accounts).data,
            200,
            {'X-Total-Count': len(b.accounts)})

@bank_api.route('/<int:id>/accounts/<int:acc_id>', methods=['DELETE'])
def delete_account(id, acc_id):
    deleted = BankAccount.query.filter(BankAccount.id==acc_id).filter(Bank.id==id).delete()
    if deleted == 0:
        abort(404)
    return '', 204
