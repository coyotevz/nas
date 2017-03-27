# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource
from ..models import Document
from .misc import IdSchema, TimestampMixin


class DocumentSchema(TimestampMixin, IdSchema):

    total = fields.Number()
    type = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    short_type = fields.String(dump_only=True)
    full_number = fields.String(dump_only=True)
    balance = fields.Number(dump_only=True)
    supplier = fields.Nested('SupplierSchema')

    class Meta:
        additional = ("point_sale", "number", "issue_date", "expiration_date",
                      "notes")

class DocumentResource(ModelResource):

    class Meta:
        name = 'documents'
        model = Document
        schema = DocumentSchema
