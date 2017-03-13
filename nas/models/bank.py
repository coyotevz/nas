# -*- coding: utf-8 -*-

from sqlalchemy.orm import validates

from . import db
from ..utils.validators import validate_cuit, validate_cbu

class Bank(db.Model):
    __tablename__ = 'bank'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True, nullable=False)
    bcra_code = db.Column(db.Unicode(8), unique=True)
    cuit = db.Column(db.Unicode(11), unique=True)
    # TODO: Add bank logo, to quickly identify

    @validates('name')
    def name_is_unique(self, key, name):
        dup = self.query.filter_by(name=name).first()
        if dup and dup.id != self.id:
            raise ValueError("Name must be unique")
        return name

    @validates('cuit')
    def cuit_is_valid(self, key, cuit):
        if not validate_cuit(cuit):
            raise ValueError('CUIT Invalid')
        dup = self.query.filter_by(cuit=cuit).first()
        if dup and dup.id != self.id:
            raise ValueError('CUIT must be unique')
        return cuit

    @validates('bcra_code')
    def bcra_code_is_unique(self, key, bcra_code):
        dup = self.query.filter_by(bcra_code=bcra_code).first()
        if dup and dup.id != self.id:
            raise ValueError("'bcra_code' must be unique")
        return bcra_code

class BankAccount(db.Model):
    __tablename__ = 'bank_account'

    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.Unicode)
    acc_type = db.Column(db.Unicode)

    number = db.Column(db.Unicode)
    owner = db.Column(db.Unicode)
    cbu = db.Column(db.Unicode)

    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)
    bank = db.relationship(Bank, backref='accounts')

    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    entity = db.relationship('Entity', backref='bank_accounts', lazy='joined')

    @validates('cbu')
    def cbu_is_valid(self, key, cbu):
        if not validate_cbu(cbu):
            raise ValueError('CBU invalid')
        return cbu
