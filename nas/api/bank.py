# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource
from ..models import Bank, BankAccount


class BankSchema(Schema):

    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    bcra_code = fields.String(lenght=8)
    cuit = fields.String(length=11)


class BankResource(ModelResource):

    class Meta:
        name = 'banks'
        model = Bank
        schema = BankSchema


class BankAccountSchema(Schema):

    id = fields.Integer(dump_only=True)
    branch = fields.String()
    acc_type = fields.String()
    number = fields.String()
    owner = fields.String()
    cbu = fields.String()


class BankAccountResource(ModelResource):

    class Meta:
        model = BankAccount
        schema = BankAccountSchema
