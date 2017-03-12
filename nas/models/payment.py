# -*- coding: utf-8 -*-

from sqlalchemy.ext.associationproxy import association_proxy

from . import db

class Payment(db.Model):
    __tablname__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.UnicodeText)

    documents = association_proxy('document_payment', 'document')

    def add_documents(self, documents):
        for document in documents:
            document.add_payment(self)


class DocumentPayment(db.Model):
    __tablename__ = 'document_payment'
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment = db.relationship(Payment, lazy='joined',
                              backref='document_payments')
    document = db.relationship('Document', lazy='joined',
                               backref='document_payments')

    def __init__(self, payment, amount):
        self.payment = payment
        self.amount = amount
