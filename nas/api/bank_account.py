# -*- coding: utf-8 -*-

from marshmallow import Schema, fields
from webargs.flaskparser import use_args

from ..utils import RestBlueprint, update_model
from ..models import BankAccount, db


bank_account_api = RestBlueprint('api.bank_account', __name__)


class BankAccountSchema(Schema):

    id = fields.Integer(dump_only=True)
    branch = fields.String()
    acc_type = fields.String()
    number = fields.String()
    owner = fields.String()
    cbu = fields.String()


@bank_account_api.route('')
def list():
    q = BankAccount.query.all()
    print("q:", q)
    return BankAccountSchema(many=True).dump(q).data, 200, {'X-Total-Count': len(q)}

@bank_account_api.route('', methods=['POST'])
@use_args(BankAccountSchema(strict=True, partial=True))
def create(properties):
    account = BankAccount(**properties)
    db.session.add(account)
    db.session.commit()
    return BankAccountSchema().dump(account).data, 201
