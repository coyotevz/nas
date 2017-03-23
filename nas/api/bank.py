# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource, Relation, Route
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

    accounts = Relation(schema=BankAccountSchema, exclude=('bank',), partial=('bank_id',))

    class Meta:
        name = 'banks'
        model = Bank
        schema = BankSchema


class BankAccountResource(ModelResource):

    class Meta:
        model = BankAccount
        schema = BankAccountSchema

    @Route.GET('/types')
    def list_types(self) -> {'symbol': fields.Str(), 'name': fields.Str()}:
        return [
            { 'symbol': 'CC', 'name': 'Cuenta Corriente' },
            { 'symbol': 'CA', 'name': 'Caja de Ahorro' },
            { 'symbol': 'CU', 'name': 'Cuenta Única' },
        ]
