# -*- coding: utf-8 -*-

from flask import Blueprint, make_response, json, current_app


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
