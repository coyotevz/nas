# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource, Relation
from ..models import Bank, BankAccount


class BankSchema(Schema):

    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    bcra_code = fields.String(lenght=8)
    cuit = fields.String(length=11)


class BankAccountSchema(Schema):

    id = fields.Integer(dump_only=True)
    bank_id = fields.Integer(required=True, load_only=True)
    entity_id = fields.Integer(required=True, load_only=True)
    branch = fields.String()
    acc_type = fields.String()
    number = fields.String()
    owner = fields.String()
    cbu = fields.String()

    bank = fields.Nested(BankSchema, exclude=('accounts'))


class BankResource(ModelResource):

    accounts = Relation(schema=BankAccountSchema, exclude=('bank',))

    class Meta:
        name = 'banks'
        model = Bank
        schema = BankSchema


class BankAccountResource(ModelResource):

    class Meta:
        model = BankAccount
        schema = BankAccountSchema
