# -*- coding: utf-8 -*-

from marshmallow import fields

from ..tonic import ModelResource, Relation, Route
from ..models import Bank, BankAccount
from .misc import IdSchema


class BankSchema(IdSchema):

    name = fields.String(required=True)
    bcra_code = fields.String(lenght=8)
    cuit = fields.String(length=11)


class BankAccountSchema(IdSchema):

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
    def list_types(self) -> {'types': fields.Dict()}:
        return {
            "types": {
                "CC": "Cuenta Corriente",
                "CA": "Caja de Ahorro",
                "CU": "Cuenta Única",
            }
        }
