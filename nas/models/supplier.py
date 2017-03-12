# -*- coding: utf-8 -*-

from decimal import Decimal
from sqlalchemy.ext.associationproxy import association_proxy

from . import db
from .entity import Entity
from .fiscal import FiscalData
from .document import Document
#from .product import ProductSupplierInfo

class Supplier(Entity):
    __tablename__ = 'supplier'
    __mapper_args__ = {'polymorphic_identity': 'supplier'}

    TYPE_PRODUCTS = 'TYPE_PRODUCTS'
    TYPE_SERVICES = 'TYPE_SERVICES'
    TYPE_SUPPLIES = 'TYPE_SUPPLIES'

    _sup_type = {
        TYPE_PRODUCTS: 'Productos',
        TYPE_SERVICES: 'Servicios',
        TYPE_SUPPLIES: 'Insumos',
    }

    supplier_id = db.Column(db.Integer, db.ForeignKey('entity.id'),
                            primary_key=True)
    rz = Entity._name_1
    name = Entity._name_2
    web = db.Column(db.Unicode, default=None)

    sup_type = db.Column(db.Enum(*_sup_type.keys(), name='supplier_type'),
                         default=TYPE_PRODUCTS)

    fiscal_data_id = db.Column(db.Integer, db.ForeignKey('fiscal_data.id'))
    fiscal_data = db.relationship(FiscalData,
                                  backref=db.backref('entity', uselist=False))

    payment_term = db.Column(db.Integer) # in days
    leap_time = db.Column(db.Integer) # in days
    delivery_included = db.Column(db.Boolean)

    supplier_contacts = db.relationship('SupplierContact',
                                        cascade='all, delete-orphan',
                                        backref='supplier')
    contacts = association_proxy('supplier_contacts', 'contact')

    debt = db.Column(db.Numeric(10, 2))
    expired = db.Column(db.Numeric(10, 2))
    expiration_date = db.Column(db.DateTime, default=None)

    #: 'bank_accounts' attribute added by BankAccount.supplier relation
    #: 'orders' attribute added by PurchaseOrder.supplier relation
    #: 'documents' attribute added by Document.supplier relation

    #: Inherited from Entity
    #: - address (collection)
    #: - email (collection)
    #: - phone (collection)
    #: - extra field (collection)

#    products = association_proxy('products_info', 'product')


    def add_contact(self, contact, role):
        self.supplier_contacts.append(SupplierContact(contact, role))

#    def add_product(self, product, **kwargs):
#        self.products_info.append(ProductSupplierInfo(product=product, **kwargs))

    @property
    def type(self):
        return self._sup_type.get(self.sup_type)

    @property
    def full_name(self):
        n = " ({0})".format(self.name) if self.name else ''
        return "{0}{1}".format(self.rz, n)

    def _update_expiration_date(self):
        doc = self.documents\
                .filter(Document.doc_status.in_([Document.STATUS_PENDING,
                                                 Document.STATUS_EXPIRED]))\
                .order_by(Document.expiration_date.asc())\
                .first()
        if doc:
            self.expiration_date = doc.expiration_date
        else:
            self.expiration_date = None

@db.event.listens_for(Supplier, "init")
def supplier_init(target, args, kwargs):
    # Sets defaults to instance
    if 'delivery_included' not in kwargs:
        target.delivery_included = False
    if 'debt' not in kwargs:
        target.debt = Decimal(0)
    if 'expired' not in kwargs:
        target.expired = Decimal(0)


class SupplierContact(db.Model):
    __tablename__ = 'supplier_contact'
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'),
                            primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.contact_id'),
                           primary_key=True)
    role = db.Column(db.Unicode)

    contact = db.relationship('Contact', backref='supplier_contacts',
                              lazy='joined')

    def __init__(self, contact, role):
        self.contact = contact
        self.role = role
