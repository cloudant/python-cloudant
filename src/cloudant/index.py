#!/usr/bin/env python
"""
_index_

Support for accessing couchdb indexes such as _all_docs
and views

"""
import json
import types

from collections import Sequence
from .errors import CloudantArgumentError


ARG_TYPES = {
    "descending": bool,
    "endkey": (basestring, Sequence),
    "endkey_docid": basestring,
    "group": bool,
    "group_level": basestring,
    "include_docs": bool,
    "inclusive_end": bool,
    "key": (int, basestring, Sequence),
    "limit": (int, types.NoneType),
    "reduce": bool,
    "skip": (int, types.NoneType),
    "stale": basestring,
    "startkey": (basestring, Sequence),
    "startkey_docid": basestring,
}

TYPE_CONVERTERS = {
    basestring: lambda x: json.dumps(x),
    str: lambda x: json.dumps(x),
    unicode: lambda x: json.dumps(x),
    Sequence: lambda x: json.dumps(list(x)),
    list:  lambda x: json.dumps(x),
    tuple: lambda x: json.dumps(list(x)),
    int: lambda x:x,
    bool: lambda x: 'true' if x else 'false',
    types.NoneType: lambda x:x
}


def python_to_couch(options):
    """
    _python_to_couch_

    Translator method to flip python style
    options into couch query options, eg True => 'true'
    """
    result = {}
    for k, v in options.iteritems():
        if k not in ARG_TYPES:
            msg = "Invalid Argument {0}".format(k)
            raise CloudantArgumentError(msg)
        if not isinstance(v, ARG_TYPES[k]):
            msg = "Argument {0} not instance of expected type: {1}".format(
                k,
                ARG_TYPES[k]
            )
            raise CloudantArgumentError(msg)
        arg_converter = TYPE_CONVERTERS.get(type(v))
        if k == 'stale':
            if v not in ('ok', 'update_after'):
                msg = (
                    "Invalid value for stale option {0} "
                    "must be ok or update_after"
                ).format(v)
                raise CloudantArgumentError(msg)
        try:
            if v is None:
                result[k] = None
            else:
                result[k] = arg_converter(v)
        except Exception as ex:
            msg = "Error converting arg {0}: {1}".format(k, ex)
            raise CloudantArgumentError(msg)

    return result


def type_or_none(typerefs, value):
    """helper to check that value is of the types passed or None"""
    return isinstance(value, typerefs) or value is None


class Index(object):
    """
    _Index_

    Sliceable and iterable interface to CouchDB View like things.

    Instantiated with the raw data callable such as the
    CloudantDatabase.all_docs or View.__call__ reference used to
    retrieve data, the index can also store optional extra args for
    customisation and supports efficient, paged iteration over the
    results to avoid large views blowing up memory

    """
    def __init__(self, method_ref, **options):
        self.options = options
        self._ref = method_ref
        self._page_size = options.pop("page_size", 100)
        self._valid_args = ARG_TYPES.keys()

    def __getitem__(self, key):
        """
        implement key access and slicing.

        key can be either a single value as a string or list which will be
        passed as the key to the query for entries matching that key or
        a slice object.

        Slices with integers will be interpreted as skip:limit-skip style pairs,
        eg with [100:200] meaning skip 100, get next 100 records so that you get
        the range between the supplied slice values

        Slices with strings/lists will be interpreted as startkey/endkey
        style keys.

        """
        if isinstance(key, basestring):
            data = self._ref(key=key, **self.options)
            return data['rows']

        if isinstance(key, list):
            data = self._ref(key=key, **self.options)
            return data['rows']

        if isinstance(key, slice):
            # slice is startkey and endkey if str or array
            str_or_none_start = type_or_none((basestring, list), key.start)
            str_or_none_stop = type_or_none((basestring, list), key.stop)
            if str_or_none_start and str_or_none_stop:
                # startkey/endkey
                if key.start is not None and key.stop is not None:
                    data = self._ref(
                        startkey=key.start,
                        endkey=key.stop,
                        **self.options
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(startkey=key.start, **self.options)
                if key.start is None and key.stop is not None:
                    data = self._ref(endkey=key.stop, **self.options)
                if key.start is None and key.stop is None:
                    data = self._ref(**self.options)
                return data['rows']
            # slice is skip:skip+limit if ints
            int_or_none_start = type_or_none(int, key.start)
            int_or_none_stop = type_or_none(int, key.stop)
            if int_or_none_start and int_or_none_stop:
                if key.start is not None and key.stop is not None:
                    limit = key.stop - key.start
                    data = self._ref(
                        skip=key.start,
                        limit=limit,
                        **self.options
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(skip=key.start, **self.options)
                if key.start is None and key.stop is not None:
                    data = self._ref(limit=key.stop, **self.options)
                # both None case handled above
                return data['rows']
        msg = (
            "Failed to interpret the argument {0} passed to "
            "Index.__getitem__ as a key value or as a slice"
        ).format(key)
        raise CloudantArgumentError(msg)

    def __iter__(self):
        """
        Implement iteration protocol by calling the
        data method accessor and paging through the responses

        Custom iteration ranges can be controlled via the ctor options

        """
        # TODO custom options need to be converted to couch friendly things
        #     eg if iteration by page is between a start key and end key
        #     verify that paging between startkey/endkey and integer
        #     indexes works
        # ALSO: Implement this
