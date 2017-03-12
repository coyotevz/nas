# -*- coding: utf-8 -*-

from decimal import Decimal
from . import db
from .payment import DocumentPayment
from .misc import TimestampMixin


class Document(db.Model, TimestampMixin):
    __tablename__ = 'document'

    TYPE_FACTURA_A = 'TYPE_FACTURA_A'
    TYPE_NOTA_CREDITO_A = 'TYPE_NOTA_CREDITO_A'
    TYPE_PRESUPUESTO = 'TYPE_PRESUPUESTO'

    _doc_type = {
        TYPE_FACTURA_A: ('Factura A', 'FAC'),
        TYPE_NOTA_CREDITO_A: ('Nota de Crédito', 'NCR'),
        TYPE_PRESUPUESTO: ('Presupuesto', 'PRE'),
    }

    STATUS_PENDING = 'STATUS_PENDING'
    STATUS_EXPIRED = 'STATUS_EXPIRED'
    STATUS_PAID = 'STATUS_PAID'

    _doc_status = {
        STATUS_PENDING: 'Pendiente',
        STATUS_EXPIRED: 'Vencida',
        STATUS_PAID: 'Pagada',
    }

    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.Enum(*_doc_type.keys(), name='doc_type'),
                         default=TYPE_FACTURA_A)
    point_sale = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    doc_status = db.Column(db.Enum(*_doc_status.keys(), name='doc_status'),
                           default=STATUS_PENDING)
    issue_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    notes = db.Column(db.UnicodeText)

    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'),
                            nullable=False)
    supplier = db.relationship('Supplier', backref=db.backref('documents',
                               order_by='Document.issue_date.asc()',
                               lazy='dynamic'))

    #: document_payments added by DocumentPayment.document relationship

    def add_payment(self, payment, amount=None):
        if amount is None:
            amount = min([payment.amount, self.balance])
        self.document_payments.append(DocumentPayment(payment, amount))

    @property
    def type(self):
        return self._doc_type.get(self.doc_type)[0]

    @property
    def short_type(self):
        return self._doc_type.get(self.doc_type)[1]

    @property
    def status(self):
        return self._doc_status.get(self.doc_status)

    @property
    def full_number(self):
        return "{:04d}-{:08d}".format(self.point_sale, self.number)

    @property
    def cancelled_date(self):
        if self.state in (self.STATUS_PENDING, self.STATUS_EXPIRED):
            return None
        return Payment.query.join('document_payment')\
                            .filter(DocumentPayment.document==self)\
                            .order_by(Payment.date.desc())[0].date

    @property
    def balance(self):
        paid = db.session.query(db.func.sum(DocumentPayment.amount))\
                         .filter(DocumentPayment.document==self).scalar()\
                         or Decimal(0)
        return self.total - paid

    def __repr__(self):
        return "<Document '{} {}' of '{}' ({})>".format(
                self.type, self.full_number, self.supplier.rz, self.status)


@db.event.listens_for(Document.supplier, "set", active_history=True)
def set_supplier(target, value, oldvalue, initiator):
    # target: Document
    # value: Supplier
    if target.doc_status in ('STATUS_PENDING', None):
        value.debt += target.total
        value._update_expiration_date()
        if oldvalue:
            oldvalue.debt -= target.total
            oldvalue._update_expiration_date()
    elif target.doc_status is 'STATUS_EXPIRED':
        value.debt += target.total
        value.expired += target.total
        value._update_expiration_date()
        if oldvalue:
            oldvalue.debt -= target.total
            oldvalue.expired -= targe.total
            oldvalue._update_expiration_date()


@db.event.listens_for(Document.doc_status, "set", active_history=True)
def set_doc_status(target, value, oldvalue, initiator):
    # target: Document
    # value: doc_status
    if target.supplier:
        if oldvalue == 'STATUS_EXPIRED':
            if value == 'STATUS_PAID':
                target.supplier.expired -= target.total
                target.supplier.debt -= target.total
                target.supplier._update_expiration_date()
            elif value == 'STATUS_PENDING':
                target.supplier.expired -= target.total
        elif oldvalue == 'STATUS_PENDING':
            if value == 'STATUS_PAID':
                target.supplier.debt -= target.total
                _update_expiration_date(target.supplier)
            elif value == 'STATUS_EXPIRED':
                target.supplier.expired += target.total
        elif oldvalue == 'STATUS_PAID':
            if value == 'STATUS_PENDING':
                target.supplier.debt += target.total
                target.supplier._update_expiration_date()
            elif value == 'STATUS_EXPIRED':
                target.supplier.debt += target.total
                target.supplier.expired += target.total
                target.supplier._update_expiration_date()

@db.event.listens_for(Document.total, "set", active_history=True)
def set_total(target, value, oldvalue, initiator):
    # target: Document
    # value: total
    if target.supplier:
        if target.doc_status in ('STATUS_PENDING', None):
            target.supplier.debt += (value - oldvalue)
        if target.doc_status is 'STATUS_EXPIRED':
            target.supplier.debt += (value - oldvalue)
            target.supplier.expired += (value - oldvalue)
