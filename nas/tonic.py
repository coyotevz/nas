# -*- coding: utf-8 -*-

import inspect
import collections
from types import MethodType
from functools import wraps, partial

from flask import current_app, make_response, json, jsonify, request, url_for, abort
from flask_sqlalchemy import get_state
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import Conflict, NotFound, InternalServerError, UnprocessableEntity, HTTPException
from werkzeug.http import HTTP_STATUS_CODES
from sqlalchemy import and_, inspect as sa_inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.exc import NoResultFound
from marshmallow import fields, Schema
from marshmallow.compat import with_metaclass
from marshmallow.utils import is_collection
from webargs.flaskparser import parser


HTTP_METHODS = ('GET', 'PUT', 'POST', 'PATCH', 'DELETE')

HTTP_METHOD_VERB_DEFAULTS = {
    'GET': 'read',
    'PUT': 'create',
    'POST': 'create',
    'PATCH': 'update',
    'DELETE': 'destroy',
}


# exceptions
class TonicException(Exception):
    werkzeug_exception = InternalServerError

    @property
    def status_code(self):
        return self.werkzeug_exception.code

    def as_dict(self):
        return {
            'status': self.status_code,
            'message': HTTP_STATUS_CODES.get(self.status_code, '')
        }

    def get_response(self):
        response = jsonify(self.as_dict())
        response.status_code = self.status_code
        return response


class ItemNotFound(TonicException):
    werkzeug_exception = NotFound

    def __init__(self, resource, where=None, id=None):
        super(ItemNotFound, self).__init__()
        self.resource = resource
        self.id = id
        self.where = where

    def as_dict(self):
        dct = super(ItemNotFound, self).as_dict()

        if self.id is not None:
            dct['item'] = {
                "$type": self.resource.meta.name,
                "$id": self.id
            }
        else:
            dct['item'] = {
                    "$type": self.resource.meta.name,
                    "$where": {
                        condition.attribute: {
                            "${}".format(condition.filter.name): condition.value
                        } if condition.filter.name is not None else condition.value
                        for condition in self.where
                    } if self.where else None
            }
        return dct


class BackendConflict(TonicException):
    werkeug_exception = Conflict

    def __init__(self, **kwargs):
        self.data = kwargs

    def as_dict(self):
        dct = super(BackendConflict, self).as_dict()
        dct.update(self.data)
        return dct


# api object code
def to_camel_case(s):
    return s[0].lower() + s.title().replace('_', '')[1:] if s else s


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def _register_view(app, rule, view_func, endpoint, methods):
    app.add_url_rule(rule,
                     view_func=view_func,
                     endpoint=endpoint,
                     methods=methods)


class Api(object):

    def __init__(self, app=None, prefix=None):
        self.prefix = prefix or ''
        self.resources = {}
        self.views = []

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        for rule, view_func, endpoint, methods in self.views:
            _register_view(app, rule, view_func, endpoint, methods)

        app.handle_exception = partial(self._exception_handler,
                                       app.handle_exception)
        app.handle_user_exception = partial(self._exception_handler,
                                            app.handle_user_exception)

    def add_route(self, route, resource, endpoint=None):
        endpoint = endpoint or '_'.join((resource.meta.name, route.relation))
        methods = [route.method]
        rule = route.build_rule(resource)

        view_func = route.build_view(endpoint, resource)

        if self.app:
            _register_view(self.app, rule, view_func, endpoint, methods)
        else:
            self.views.append((rule, view_func, endpoint, methods))

    def register_resource(self, resource):
        if resource in self.resources.values():
            return

        if resource.api is not None and resource.api != self:
            raise RuntimeError

        # check that each resource has an associated manager
        if issubclass(resource, ModelResource) and resource.manager is None:
            resource.manager = Manager(resource, resource.meta.get('model'))

        resource.api = self
        resource.route_prefix = ''.join((self.prefix, '/', resource.meta.name))

        for route in resource.routes.values():
            self.add_route(route, resource)

        for name, rset in inspect.getmembers(resource, lambda m: isinstance(m, RouteSet)):
            if rset.attribute is None:
                rset.attribute = name

            for i, route in enumerate(rset.routes(name)):
                if route.attribute is None:
                    route.attribute = '{}_{}'.format(rset.attribute, i)
                resource.routes['{}_{}'.format(rset.attribute, route.relation)] = route
                self.add_route(route, resource)

        self.resources[resource.meta.name] = resource

    def _exception_handler(self, original_handler, e):
        if isinstance(e, TonicException):
            return e.get_response()

        if not request.path.startswith(self.prefix):
            return original_handler(e)

        if isinstance(e, HTTPException):

            # handle UnprocessableEntity.data attribute (validation errors)
            data = getattr(e, 'data', None)
            if data:
                messages = data['messages']
            else:
                messages = e.description

            return _make_response({
                'status': e.code,
                'messages': messages
            }, e.code)

        return original_handler(e)

# querysting sort & filters code
_keywords = ('page', 'per_page', 'sort', 'fields', 'include')

OPERATORS = {
    # operators which accepts a single argument
    'is_null': lambda f: f == None,
    'is_not_null': lambda f: f != None,

    # operators which accepts two arguments
    'eq': lambda f, a: f == a,
    'ne': lambda f, a: f != a,
    'gt': lambda f, a: f > a,
    'lt': lambda f, a: f < a,
    'gte': lambda f, a: f >= a,
    'lte': lambda f, a: f <= a,

    'contains': lambda f, a: f.contains(a),
    'endswith': lambda f, a: f.endswith(a),
    'startswith': lambda f, a: f.startswith(a),
    'like': lambda f, a: f.like(a),
    'ilike': lambda f, a: f.ilike(a),

    'in': lambda f, a: f.in_(a),
    'nin': lambda f, a: ~f.in_(a),

    # operators which accepts three arguments
    'has': lambda f, a, fn: f.has(**{fn: a}),
    'any': lambda f, a, fn: f.any(**{fn: a})
}

SORT_ORDER = {
    'asc': lambda f: f.asc,
    'desc': lambda f: f.desc,
}

class Filter(object):
    __slot__ = ()

    def __init__(self, name, operator, argument=None, other=None):
        self.name = name
        self.operator = operator
        self.argument = argument
        self.other = other

    def __repr__(self):
        return 'Filter("{}", "{}", "{}")'.format(self.name, self.operator, self.argument)

    def expression(self, model):
        return OPERATORS[self.operator](getattr(model, self.name), self.argument)

def parse_param(key, value):
    key, op = (key.rsplit(':', 1) + ['eq'])[:2]
    if key not in _keywords:
        value = Filter(key, op, value)
        key = 'where'
    elif key == 'sort':
        if op not in SORT_ORDER.keys():
            op = 'asc'
        value = (op, value)
    elif key in ('page', 'per_page'):
        value = int(value)
    return key, value


def parse_querystring():
    params = {}
    for key, value in request.args.items(multi=True):
        k, v = parse_param(key, value)
        params.setdefault(k, []).append(v)

    # unroll
    for k in ('page', 'per_page'):
        if k in params:
            params[k] = params[k][0]

    return params


# routes code
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


def _unpack(value):
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


def build_schema(schema_or_dict):
    if isinstance(schema_or_dict, dict):
        return type('DictSchema', (Schema,), schema_or_dict)
    return schema_or_dict


class Route(object):

    def __init__(self, method=None, view_func=None, rule=None, attribute=None,
                 rel=None, request_schema=None, response_schema=None, **schema_kw):
        self.method = method
        self.view_func = view_func
        self.rule = rule
        self.attribute = attribute
        self.rel = rel
        self.endpoint = None

        annotations = getattr(view_func, '__annotations__', None)

        if isinstance(annotations, dict) and len(annotations):
            self.response_schema = annotations.get('return', response_schema)
        else:
            self.response_schema = response_schema

        self.response_schema = build_schema(self.response_schema)
        self.request_schema = request_schema

        self._schema_kw = schema_kw

        # Rewrite 'http methods' as instance methods, Route().GET
        for method in HTTP_METHODS:
            setattr(self, method, MethodType(_method_decorator(method), self))

    @property
    def relation(self):
        if self.rel:
            return self.rel
        else:
            verb = HTTP_METHOD_VERB_DEFAULTS.get(self.method, self.method.lower())
            return "{}_{}".format(verb, self.attribute)

    def for_method(self, method, view_func, rel=None, **kwargs):
        attribute = kwargs.pop('attribute', self.attribute)

        instance = self.__class__(method,
                                  view_func=view_func,
                                  rule=self.rule,
                                  rel=rel,
                                  attribute=attribute,
                                  **kwargs)
        return instance

    def __get__(self, obj, owner):
        if obj is None:
            return self
        return lambda *args, **kwargs: self.view_func(obj, *args, **kwargs)

    def build_rule(self, resource, relative=False):
        """Returns a URL rule string for this route and resource."""
        rule = self.rule

        if rule is None:
            rule = '/{}'.format(self.attribute)
        elif callable(rule):
            rule = rule(resource)

        if relative or resource.route_prefix is None:
            return rule[1:]

        return ''.join((resource.route_prefix, rule))

    def build_view(self, name, resource):
        """Returns a view function for all links within this route and resource."""
        # keep track of endpoint assigned
        self.endpoint = name
        view_func = self.view_func
        response_schema = self.response_schema or resource.meta.schema
        schema_kw = self._schema_kw

        if isinstance(response_schema, type): # cls or instance
            response_schema = response_schema(**self._schema_kw)

        def view(*args, **kwargs):
            instance = resource()
            # Oportunity to parse arguments and format response
            if request.method in ('POST', 'PATCH'):
                request_schema = self.request_schema or resource.meta.schema

                # dirty hack
                if isinstance(request_schema, type):
                    skwargs = {**{'strict': True, 'partial': request.method=='PATCH'}, **schema_kw}
                    request_schema = request_schema(**skwargs)

                parsed_args = parser.parse(request_schema, locations=('json',))
                args = args + (parsed_args,)
            elif request.method in ('GET',):
                kwargs.update(parse_querystring())
            resp = view_func(instance, *args, **kwargs)

            if isinstance(resp, BaseResponse):
                return resp

            data, code, headers = _unpack(resp)
            result = response_schema.dump(data, many=is_collection(data)).data
            return _make_response(result, code, headers)
        return view


def _method_decorator(method):
    def wrapper(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return self.for_method(method, args[0], **kwargs)
        else:
            return lambda f: self.for_method(method, f, *args, **kwargs)

    wrapper.__name__ = method
    return wrapper

def _route_decorator(method):
    @classmethod
    def decorator(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return cls(method, args[0])
        else:
            return lambda f: cls(method, f, *args, **kwargs)

    decorator.__name__ = method
    return decorator

# Attach 'http methods' as classmethods, Route.GET
for method in HTTP_METHODS:
    setattr(Route, method, _route_decorator(method))


class ItemRoute(Route):

    def build_rule(self, resource, relative=False):
        rule = self.rule
        id_matcher = '<int:id>'

        if rule is None:
            rule = '/{}'.format(self.attribute)
        elif callable(rule):
            rule = rule(resource)

        if relative or resource.route_prefix is None:
            return rule[1:]

        return ''.join((resource.route_prefix, '/', id_matcher, rule))

    def build_view(self, name, resource):
        original_view = super(ItemRoute, self).build_view(name, resource)

        def view(*args, **kwargs):
            id = kwargs.pop('id')
            item = resource.manager.read(id)
            return original_view(item, *args, **kwargs)

        return view


class RouteSet(object):
    """
    An abstract class for combining related routes, this mark a resource member
    as a Route.
    """

    def routes(self):
        return ()


class Relation(RouteSet):

    def __init__(self, attribute=None, schema=None, methods=None, **schema_kw):
        self.attribute = attribute
        self.schema = schema
        self.schema_kw = schema_kw
        self.methods = methods

    def routes(self, name=None):
        rule = '/{}'.format(name or self.attribute)

        relation_route = ItemRoute(rule='{}/<int:target_id>'.format(rule))
        relations_route = ItemRoute(rule=rule)

        def relation_instances(resource, item, **kwargs):
            return resource.manager.relation_instances(item, self.attribute, **kwargs)

        yield relations_route.for_method('GET', relation_instances,
                                         rel="read_{}".format(self.attribute),
                                         response_schema=self.schema,
                                         **self.schema_kw)

        def relation_add(resource, item, target_data):
            target_item = resource.manager.relation_add(item, self.attribute, target_data)
            resource.manager.commit()
            return target_item

        post_schema_kw = {**{'strict': True, 'partial': True}, **self.schema_kw}

        yield relations_route.for_method('POST', relation_add,
                                         rel='add_{}'.format(self.attribute),
                                         request_schema=self.schema,
                                         response_schema=self.schema,
                                         **post_schema_kw)

        def relation_remove(resource, item, target_id):
            resource.manager.relation_remove(item, self.attribute, target_id)
            resource.manager.commit()
            return None, 204

        yield relation_route.for_method('DELETE', relation_remove,
                                        rel='remove_{}'.format(self.attribute))


# manager code

def _get_target_model(instance, attribute):
    prop = sa_inspect(instance.__class__).relationships.get(attribute, None)
    if not prop:
        return None
    return prop.mapper.class_

class Manager(object):
    """
    A layer that provides basic CRUD operations over resource associated
    model.
    """

    def __init__(self, resource, model):
        self.resource = resource

        # attach manager to resource
        resource.manager = self

        self._init_model(resource, model, resource.meta)
        #self.filters = resource_filters(resource, resource.meta)

    def _init_model(self, resource, model, meta):
        mapper = class_mapper(model)
        self.model = model

        if meta.id_attribute:
            self.id_column = getattr(model, meta.id_attribute)
            self.id_attribute = meta.id_attribute
        else:
            self.id_column = mapper.primary_key[0]
            self.id_attribute = self.id_column.name

        self.default_sort_expression = self.id_column.asc()

        if not hasattr(resource.Meta, 'name'):
            meta['name'] = model.__tablename__.lower()

    def instances(self, where=None, sort=None, **kwargs):
        query = self._query()

        if query is None:
            return []

        if where:
            expressions = [self._expression_for_condition(condition) for condition in where]
            query = self._query_filter(query, self._and_expression(expressions))

        return self._query_order_by(query, sort)

    def first(self, where=None, sort=None):
        try:
            return self._query_get_first(self.instances(where, sort))
        except IndexError:
            raise ItemNotFound(self.resource, where=where)

    def read(self, id):
        query = self._query()

        if query is None:
            raise ItemNotFound(self.resource, id=id)
        return self._query_filter_by_id(query, id)

    def create(self, properties, commit=True):
        item = self.model()

        for key, value in properties.items():
            setattr(item, key, value)

        session = self._get_session()

        try:
            session.add(item)
            if commit:
                session.commit()
        except IntegrityError as e:
            session.rollback()
            if current_app.debug:
                raise BackendConflict(
                        debug_info=dict(exception_message=str(e),
                                        statement=e.statement,
                                        params=e.params))
            raise BackendConflict()

        return item

    def update(self, item, changes, commit=True):
        session = self._get_session()

        actual_changes = {
            key: value for key, value in changes.items()
            if self._is_change(getattr(item, key, None), value)
        }

        try:
            for key, value in changes.items():
                setattr(item, key, value)

            if commit:
                session.commit()
        except IntegrityError as e:
            session.rollback()
            if current_app.debug:
                raise BackendConflict(
                        debug_info=dict(exception_message=str(e),
                                        statement=e.statement,
                                        params=e.params))
            raise BackendConflict()

        return item

    def delete(self, item):
        session = self._get_session()

        try:
            session.delete(item)
            session.commit()
        except IntegrityError as e:
            session.rollback()

            raise BackendConflict()

    def relation_instances(self, item, attribute, **kwargs):
        # TODO: Honor where, sort, fields, etc. arguments
        query = getattr(item, attribute)

        if isinstance(query, InstrumentedList):
            return query

        return self._query_get_all(query)

    def relation_add(self, item, attribute, target_data):
        Model = _get_target_model(item, attribute)
        if Model is None:
            abort(404)
        target_item = Model(**target_data)
        getattr(item, attribute).append(target_item)
        return target_item

    def relation_remove(self, item, attribute, target_id):
        # TODO: Rewrite using _get_remote_model
        target_prop = sa_inspect(item.__class__).relationships.get(attribute, None)
        if not target_prop:
            abort(404)
        target_model = target_prop.mapper.class_
        remote_col = list(target_prop.remote_side)[0]
        del_query = target_model.query.filter(remote_col==item.id).filter(target_model.id==target_id)
        deleted = del_query.delete()
        if deleted == 0:
            abort(404)

    def commit(self):
        session = self._get_session()
        session.commit()

    @staticmethod
    def _get_session():
        return get_state(current_app).db.session

    @staticmethod
    def _is_change(a, b):
        return (a is None) != (b is None) or a != b

    def _query(self):
        return self.model.query

    def _query_filter(self, query, expression):
        return query.filter(expression)

    def _expression_for_condition(self, condition):
        return condition.expression(self.model)

    def _and_expression(self, expressions):
        if not expressions:
            return False
        if len(expressions) == 1:
            return expressions[0]
        return and_(*expressions)

    def _query_filter_by_id(self, query, id):
        try:
            return query.filter(self.id_column == id).one()
        except NoResultFound:
            raise ItemNotFound(self.resource, id=id)

    def _query_order_by(self, query, sort=None):
        order_clauses = []

        if not sort:
            return query.order_by(self.default_sort_expression)

        for order, attribute in sort:
            column = getattr(self.model, attribute, None)
            if column:
                order_clauses.append(getattr(column, order)())

        return query.order_by(*order_clauses)

    def _query_get_all(self, query):
        return query.all()

    def _query_get_first(self, qurey):
        try:
            return query.one()
        except NotResultFound:
            raise IndexError()

def _add_route(routes, route, name):
    if route.attribute is None:
        route.attribute = name

    routes[route.relation] = route

# resource code
class ResourceMeta(type):

    def __new__(cls, name, bases, members):
        new_cls = super(ResourceMeta, cls).__new__(cls, name, bases, members)
        routes = {}
        meta = AttributeDict()

        for base in bases:
            meta.update(getattr(base, 'meta', {}) or {})
            for n, m in inspect.getmembers(base, lambda m: isinstance(m, Route)):
                _add_route(routes, m, n)

        if 'Meta' in members:
            opts = members['Meta'].__dict__
            meta.update({k: v for k, v in opts.items()
                         if not k.startswith('__')})
            if not opts.get('name', None):
                meta['name'] = name.lower()
        else:
            meta['name'] = name.lower()

        for n, m in members.items():
            if isinstance(m, Route):
                _add_route(routes, m, n)

        new_cls.routes = routes
        new_cls.meta = meta
        return new_cls

class Resource(with_metaclass(ResourceMeta, object)):

    api = None
    route_prefix = None


class ModelResource(Resource):

    manager = None

    class Meta:
        id_attribute = None     # use 'id' by default
        filters = True

    def _location_for(self, id):
        read_view = self.routes['self']
        if read_view.endpoint:
            return {'Location': url_for(read_view.endpoint, id=id)}
        return {}

    @Route.GET('', rel="instances")
    def instances(self, **kwargs):
        return self.manager.instances(**kwargs)

    @instances.POST(rel="create")
    def create(self, properties):
        item = self.manager.create(properties)
        return item, 201, self._location_for(item.id)

    @Route.GET('/<int:id>', rel="self", attribute="instance")
    def read(self, id, **kwargs):
        return self.manager.read(id)

    @read.PATCH(rel="update")
    def update(self, properties, id):
        item = self.manager.read(id)
        updated_item = self.manager.update(item, properties)
        return updated_item

    @update.DELETE(rel="destroy")
    def destroy(self, id):
        item = self.manager.read(id)
        self.manager.delete(item)
        return None, 204
