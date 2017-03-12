# -*- coding: utf-8 -*-

from . import db
from .misc import TimestampMixin


class PurchaseOrder(db.Model, TimestampMixin):
    __tablename__ = 'purchaseorder'

    STATUS_CANCELLED = 'STATUS_CANCELLED'
    STATUS_QUOTING = 'STATUS_QUOTING'
    STATUS_PENDING = 'STATUS_PENDING'
    STATUS_PARTIAL = 'STATUS_PARTIAL'
    STATUS_CONFIRMED = 'STATUS_CONFIRMED'
    STATUS_COMPLETED = 'STATUS_COMPLETED'
    STATUS_DRAFT = 'STATUS_DRAFT'

    _po_status = {
        STATUS_CANCELLED: 'Cancelada',
        STATUS_QUOTING: 'Valorizando',
        STATUS_PENDING: 'Pendiente',
        STATUS_PARTIAL: 'Parcial',
        STATUS_CONFIRMED: 'Confirmada',
        STATUS_COMPLETED: 'Completa',
        STATUS_DRAFT: 'Borrador',
    }

    METHOD_EMAIL = 'METHOD_EMAIL'
    METHOD_FAX = 'METHOD_FAX'
    METHOD_PHONE = 'METHOD_PHONE'
    METHOD_PERSONALLY = 'METHOD_PERSONALLY'

    _po_method = {
        METHOD_EMAIL: 'Correo Electrónico',
        METHOD_FAX: 'Fax',
        METHOD_PHONE: 'Telefónico',
        METHOD_PERSONALLY: 'Personalmente',
    }

    id = db.Column(db.Integer, primary_key=True)
    point_sale = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    po_status = db.Column(db.Enum(*_po_status.keys(), name='po_status'),
                          default=STATUS_DRAFT)
    po_method = db.Column(db.Enum(*_po_method.keys(), name='po_method'),
                          default=None)
    notes = db.Column(db.UnicodeText)


    open_date = db.Column(db.Date)
    confirm_date = db.Column(db.Date)
    receival_date = db.Column(db.Date)

    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'), nullable=False)
    supplier = db.relationship('Supplier', backref="orders")

    @property
    def status(self):
        return self._po_status[self.po_status]

    @property
    def method(self):
        return self._po_method[self.po_method]

    @property
    def full_desc(self):
        if self.point_sale == 0:
            return "Pedido {:>04d}S-{:08d}".format(self.supplier_id, self.number)
        return "Pedido {:04d}-{:08d}".format(self.point_sale, self.number)


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchaseorder_item'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.Unicode(40))
    description = db.Column(db.UnicodeText)
    quantity = db.Column(db.Integer, default=0)
    quantity_received = db.Column(db.Integer, default=0)
    quantity_returned = db.Column(db.Integer, default=0)

    order_id = db.Column(db.Integer, db.ForeignKey('purchaseorder.id'),
                         nullable=False)
    order = db.relationship('PurchaseOrder', backref='items')

    @property
    def pending_quantity(self):
        return self.quantity - self.quantity_received
