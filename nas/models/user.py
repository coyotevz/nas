# -*- coding: utf-8 -*-

from datetime import datetime

from flask_sqlalchemy import BaseQuery
from werkzeug import generate_password_hash, check_password_hash, cached_property
from sqlalchemy.ext.hybrid import hybrid_property

from . import db
from .entity import Entity


class UserQuery(BaseQuery):

    def from_identity(self, identity):
        """
        Loads user from flask_principal.Identity instance and assigns
        permission from user.

        A "user" instance is monkeypatched to the identity instance.

        If no user found then None is returned.
        """
        try:
            user = self.get(int(identity.id or 0))
        except ValueError:
            user = None

        if user:
            identity.provides.update(user.provides)

        identity.user = user
        return user

    def authenticate(self, login, password):

        user = self.filter(User.username==login).first()
        return user, user.check_password(password)


class User(Entity):
    __tablename__ = 'user'
    __mapper_args__ = {'polymorphic_identity': 'user'}

    query_class = UserQuery

    # user roles
    MEMBER = 100
    MODERATOR = 200
    ADMIN = 300

    user_id = db.Column(db.Integer, db.ForeignKey('entity.id'),
                        primary_key=True)

    first_name = Entity._name_1
    last_name = Entity._name_2

    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Integer, default=MEMBER)

    _pw_hash = db.Column('pw_hash', db.Unicode(80))

    @hybrid_property
    def password(self):
        return self._pw_hash

    @password.setter
    def password(self, password):
        self._pw_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @property
    def is_moderator(self):
        return self.role >= self.MODERATOR

    @property
    def is_admin(self):
        return self.role >= self.ADMIN
