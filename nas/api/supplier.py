# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource, Relation
from ..models import Supplier

from .misc import EntitySchema


class SupplierSchema(EntitySchema):

    rz = fields.String(attribute='_name_1')
    name = fields.String(attribute='_name_2')


class SupplierResource(ModelResource):

    class Meta:
        name = 'suppliers'
        model = Supplier
        schema = SupplierSchema
