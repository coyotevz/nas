# -*- coding: utf-8 -*-

from werkzeug.routing import BaseConverter


class ListConverter(BaseConverter):

    _subtypes = {
        'int': int,
        'str': str,
    }

    def __init__(self, url_map, subtype=None, mutable=False):
        super().__init__(url_map)
        self.subtype = subtype
        self.mutable = mutable
        if subtype:
            rearg = {'int': '\d', 'str': '\w'}[subtype]
        else:
            rearg = '[\d\w]'
        self.regex = '{0}+(?:,{0}*)+'.format(rearg)

    def to_python(self, value):
        retval = filter(None, value.split(','))
        if self.subtype in self._subtypes:
            retval = map(self._subtypes[self.subtype], retval)
        if not self.mutalbe:
            retval = tuple(retval)
        return retval

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(value) for value in values)


class RangeConverter(BaseConverter):

    regex = '\d+-\d+'

    def to_python(self, value):
        s, e = value.split('-')
        return list(range(int(s), int(e)+1))

    def to_url(self, value):
        return '-'.join([value[0], value[-1]])


class RangeListConverter(BaseConverter):

    regex = '(?:\d+|\d+-\d+)+(?:,(?:\d+|\d+-\d+))*'

    def to_python(self, value):
        retval = []
        for gr in value.split(','):
            if '-' in gr:
                s, e = gr.split('-')
                retval.extend(list(range(int(s), int(e)+1)))
            else:
                retval.append(int(gr))
        return retval

    def to_url(self, values):
        t = -1
        s = []
        segs = []
        for v in sorted(values):
            if t+1 == v:
                s.append(v)
            else:
                segs.append(s)
                s = [v]
            t = v
        outs = []
        for r in sorted(segs):
            if len(r) > 1:
                r = sorted(r)
                outs.append('{}-{}'.format(r[0], r[-1]))
            else:
                outs.append('{}'.format(r[0]))
        return ','.join(BaseConverter.to_url(out) for out in outs)
