# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from . import db


class TimestampMixin(object):

    created = db.Column(db.DateTime, default=datetime.now)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now)

    @staticmethod
    def stamp_modified(mapper, connection, target):
        if db.object_session(target).is_modified(target):
            target.modified = datetime.now()

    @classmethod
    def __declare_last__(cls):
        db.event.listen(cls, 'before_update', cls.stamp_modified)


class RefEntityMixin(object):

    @declared_attr
    def entity_id(cls):
        return db.Column('entity_id', db.Integer, db.ForeignKey('entity.id'),
                         nullable=False)

    @declared_attr
    def entity(cls):
        name = cls.__name__.lower()
        return db.relationship('Entity',
                               backref=db.backref(name, lazy='joined'))


class Address(RefEntityMixin, db.Model):
    "Stores entity's addresses information"
    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.Unicode(64), nullable=False)
    streetnumber = db.Column(db.Unicode(64))
    city = db.Column(db.Unicode(64))
    province = db.Column(db.Unicode(32), nullable=False)
    zip_code = db.Column(db.Unicode(32))
    address_type = db.Column(db.Unicode)

    def __str__(self):
        retval = self.street
        retval += " %s" % self.streetnumber if self.streetnumber else 'S/N'
        if self.city:
            retval += ", %s" % self.city
        retval +=", %s" % self.province
        if self.postal_code:
            retval += " (%s)" % self.postal_code
        return retval


class Phone(RefEntityMixin, db.Model):
    "Model to store entity's phone information"
    __tablename__ = 'phone'

    id = db.Column(db.Integer, primary_key=True)
    phone_type = db.Column(db.Unicode)
    number = db.Column(db.Unicode, nullable=False)

    def __str__(self):
        retval = self.phone_type+': ' if self.phone_type else ''
        retval += self.number
        return retval


class Email(RefEntityMixin, db.Model):
    "Model to store entity's email information"
    __tablename__ = 'email'
    id = db.Column(db.Integer, primary_key=True)
    email_type = db.Column(db.Unicode(50))
    email = db.Column(db.Unicode(50), nullable=False)

    def __str__(self):
        retval = self.email_type+': ' if self.email_type else ''
        retval += self.email
        return retval
