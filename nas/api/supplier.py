# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource, Relation
from ..models import Supplier

from .misc import EntitySchema
from .bank import BankAccountSchema


class ContactSchema(EntitySchema):

    first_name = fields.String(attribute='_name_1')
    last_name = fields.String(attribute='_name_2')
    suppliers = fields.Nested('SupplierSchema', exclude=('contacts',), many=True)


class SupplierSchema(EntitySchema):

    rz = fields.String(attribute='_name_1')
    name = fields.String(attribute='_name_2')


class SupplierResource(ModelResource):

    contacts = Relation(attribute='supplier_contacts', schema=ContactSchema, exclude=('suppliers',))
    bank_accounts = Relation(schema=BankAccountSchema)

    class Meta:
        name = 'suppliers'
        model = Supplier
        schema = SupplierSchema
