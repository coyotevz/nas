# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def configure_db(app):
    db.init_app(app)

from .entity import Entity
from .user import User
from .misc import Address, Phone, Email
from .fiscal import FiscalData
from .contact import Contact
from .supplier import Supplier, SupplierContact
from .product import Product, ProductSupplierInfo
from .document import Document
from .payment import Payment, DocumentPayment
from .bank import Bank, BankAccount
from .order import PurchaseOrder, PurchaseOrderItem
