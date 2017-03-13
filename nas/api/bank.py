# -*- coding: utf-8 -*-

from flask import Blueprint, make_response, json, current_app
from webargs.flaskparser import use_args
from marshmallow import validates, ValidationError

from ..models import Bank, db
from . import ma


class ModelSchema(ma.ModelSchema):

    def make_instance(self, data):
        return data


def update_model(model, properties):
    for pname, pvalue in properties.items():
        setattr(model, pname, pvalue)


def unpack(value):
    """Return a three tuple of data, code and headers."""
    if not isinstance(value, tuple):
        return value, 200, {}
    try:
        data, code, headers = value
        return data, code, headers
    except ValueError:
        pass
    try:
        data, code = value
        return data, code, {}
    except ValueError:
        pass
    return value, 200, {}


def _make_response(data, code, headers=None):
    settings = {}
    if current_app.debug:
        settings.setdefault('indent', 4)
        settings.setdefault('sort_keys', True)

    data = json.dumps(data, **settings)

    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    resp.headers['Content-Type'] = 'application/json'
    return resp


class RestBlueprint(Blueprint):

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__)

            def new_f(*args, **kwargs):
                resp = f(*args, **kwargs)
                data, code, headers = unpack(resp)
                return _make_response(data, code, headers)

            self.add_url_rule(rule, endpoint, new_f, **options)

            return new_f
        return decorator


bank_api = RestBlueprint('api.bank', __name__)


class BankSchema(ModelSchema):

    class Meta:
        model = Bank


@bank_api.route('')
def list():
    q = Bank.query.all()
    return BankSchema(many=True).dump(q).data, 200, {'X-Total-Count': len(q)}


@bank_api.route('', methods=['POST'])
@use_args(BankSchema(strict=True, partial=True))
def create(properties):
    if 'name' not in properties:
        raise ValueError("'name' field must be present")
    bank = Bank(**properties)
    db.session.add(bank)
    db.session.commit()
    return BankSchema().dump(bank).data, 201


@bank_api.route('/<int:id>', methods=['GET'])
def get(id):
    b = Bank.query.get_or_404(id)
    return BankSchema().dump(b).data


@bank_api.route('/<int:id>', methods=['PATCH'])
@use_args(BankSchema(strict=True, partial=True))
def update(properties, id):
    bank = Bank.query.get_or_404(id)
    update_model(bank, properties)
    db.session.commit()
    return BankSchema().dump(bank).data


@bank_api.route('/<int:id>', methods=['DELETE'])
def delete(id):
    b = Bank.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return '', 204
