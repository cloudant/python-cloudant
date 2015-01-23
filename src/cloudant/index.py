#!/usr/bin/env python
"""
_index_

Support for accessing couchdb indexes such as _all_docs
and views

"""
import json

from collections import Sequence

ALL_ARGS = [
    "descending",
    "endkey",
    "endkey_docid",
    "group",
    "group_level",
    "include_docs",
    "inclusive_end",
    "key",
    "limit",
    "reduce",
    "skip",
    "stale",
    "startkey",
    "startkey_docid"
]

BOOLEAN_ARGS = [
    'include_docs',
    'inclusive_end',
    'reduce',
    'group',
    'descending'
]

ARRAY_ARGS = [
    'startkey',
    'endkey'
]
STRING_ARGS = [
    'key',
]


def python_to_couch(options):
    """
    _python_to_couch_

    Translator method to flip python style
    options into couch query options, eg True => 'true'
    """
    for b in BOOLEAN_ARGS:
        if b in options:
            value = options[b]
            if not isinstance(value, bool):
                continue
            if value:
                options[b] = 'true'
            else:
                options[b] = 'false'
    for a in ARRAY_ARGS:
        if a in options:
            value = options[a]
            if isinstance(value, Sequence):
                options[a] = json.dumps(list(value))
            elif isinstance(value, basestring):
                options[a] = json.dumps(value)
    for s in STRING_ARGS:
        if s in options:
            if isinstance(options[s], basestring):
                options[s] = json.dumps(options[s])
    return options

def type_or_none(typerefs, value):
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
        self._valid_args = ALL_ARGS

    def _prepare_extras(self):
        """
        check that extra params are expected/valid
        """
        for k in self.options:
            if k not in self._valid_args:
                raise ValueError("Invalid argument: {0}".format(k))
        extras = python_to_couch(self.options)
        return extras

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
        extras = self._prepare_extras()
        if isinstance(key, basestring):
            data = self._ref(key=key, **extras)
            return data['rows']

        if isinstance(key, list):
            data = self._ref(key=key, **extras)
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
                        **extras
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(startkey=key.start, **extras)
                if key.start is None and key.stop is not None:
                    data = self._ref(endkey=key.stop, **extras)
                if key.start is None and key.stop is None:
                    data = self._ref(**extras)
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
                        **extras
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(skip=key.start, **extras)
                if key.start is None and key.stop is not None:
                    data = self._ref(limit=key.stop, **extras)
                # both None case handled above
                return data['rows']
        raise RuntimeError("wtf was {0}??".format(key))

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
