# -*- coding: utf-8 -*-

from sqlalchemy.ext.associationproxy import association_proxy

from . import db


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(14), nullable=False, unique=True)
    description = db.Column(db.Unicode(40), nullable=False)
    brand = db.Column(db.UnicodeText)

    suppliers = association_proxy('suppliers_info', 'supplier')


class ProductSupplierInfo(db.Model):
    __tablename__ = 'productsupplier_info'
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'), primary_key=True)
    supplier = db.relationship('Supplier', backref='products_info', lazy='joined')

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    product = db.relationship('Product', backref='suppliers_info', lazy='joined')

    code = db.Column(db.Unicode(80))
    description = db.Column(db.Unicode)
    base_cost = db.Column(db.Numeric(10, 2))
    minimum_purchase = db.Column(db.Integer, default=1)
