# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource, Route
from ..models import Document
from .misc import IdSchema, TimestampMixin


class DocumentSchema(TimestampMixin, IdSchema):

    issue_date = fields.Date()
    expiration_date = fields.Date()
    total = fields.Number()
    type = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    short_type = fields.String(dump_only=True)
    full_number = fields.String(dump_only=True)
    balance = fields.Number(dump_only=True)
    supplier = fields.Nested('SupplierSchema')

    class Meta:
        additional = ("point_sale", "number", "notes")

class DocumentResource(ModelResource):

    class Meta:
        name = 'documents'
        model = Document
        schema = DocumentSchema

    @Route.GET('/types')
    def types(self) -> {"types": fields.Dict()}:
        return {"types": Document._doc_type}

    @Route.GET('/statuses')
    def statuses(self) -> {"statuses": fields.Dict()}:
        return {"statuses": Document._doc_status}
