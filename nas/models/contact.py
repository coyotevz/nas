# -*- coding: utf-8 -*-

from sqlalchemy.ext.associationproxy import association_proxy

from . import db
from .entity import Entity

class Contact(Entity):
    __tablename__ = 'contact'
    __mapper_args__ = {'polymorphic_identity': 'contact'}
    contact_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key=True)

    first_name = Entity._name_1
    last_name = Entity._name_2

    suppliers = association_proxy('supplier_contacts', 'supplier')

    @property
    def full_name(self):
        return u' '.join([self.first_name, self.last_name])
