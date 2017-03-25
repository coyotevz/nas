# -*- coding: utf-8 -*-

from marshmallow import Schema, fields

from ..tonic import ModelResource
from ..models import Document
from .misc import IdSchema, TimestampMixin


class DocumentSchema(TimestampMixin, IdSchema):

    pass


class DocumentResource(ModelResource):

    class Meta:
        name = 'documents'
        model = Document
        schema = DocumentSchema
