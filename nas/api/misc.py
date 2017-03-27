# -*- coding: utf-8 -*-

from marshmallow import Schema, fields


class IdSchema(Schema):

    id = fields.Integer(dump_only=True)


class AddressSchema(IdSchema):

    class Meta:
        fields = ('street', 'streetnumber', 'city', 'province', 'zip_code', 'address_type')


class EmailSchema(IdSchema):

    class Meta:
        fields = ('email', 'email_type')


class PhoneSchema(IdSchema):

    class Meta:
        fields = ('number', 'phone_type')


class FiscalDataSchema(IdSchema):

    cuit = fields.String()
    type = fields.String()
    iibb = fields.String()


class TimestampMixin(object):

    created = fields.DateTime(dump_only=True)
    modified = fields.DateTime(dump_only=True)


class EntitySchema(TimestampMixin, IdSchema):

    address = fields.Nested(AddressSchema, many=True)
    email = fields.Nested(EmailSchema, many=True)
    phone = fields.Nested(PhoneSchema, many=True)
    bank_accounts = fields.Nested('BankAccountSchema', many=True)
