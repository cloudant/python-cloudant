#!/usr/bin/env python
"""
_utils_

General utilities


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


def python_to_couch(kwargs):
    """
    _python_to_couch_

    Translator method to flip python style
    options into couch query options, eg True => 'true'
    """
    for b in BOOLEAN_ARGS:
        if b in kwargs:
            if kwargs[b]:
                kwargs[b] = 'true'
            else:
                kwargs[b] = 'false'
    for a in ARRAY_ARGS:
        if a in kwargs:
            value = kwargs[a]
            if isinstance(value, Sequence):
                kwargs[a] = json.dumps(list(value))
            elif isinstance(value, basestring):
                kwargs[a] = json.dumps(value)
    for s in STRING_ARGS:
        if s in kwargs:
            kwargs[s] = json.dumps(kwargs[s])
    return kwargs


class Index(object):
    """
    _Index_

    Sliceable and iterable interface to CouchDB View like things

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
        implement key access and slicing


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
            str_or_none_start = isinstance(key.start, (basestring, list)) or key.start is None
            str_or_none_stop =  isinstance(key.stop, (basestring, list)) or key.stop is None
            if str_or_none_start and str_or_none_stop:
                # startkey/endkey
                if key.start is not None and key.stop is not None:
                    data = self._ref(startkey=key.start, endkey=key.stop)
                if key.start is not None and key.stop is None:
                    data = self._ref(startkey=key.start)
                if key.start is None and key.stop is not None:
                    data = self._ref(endkey=key.stop)
                if key.start is None and key.stop is None:
                    data = self._ref()
                return data['rows']
            # slice is skip:limit if ints
            int_or_none_start = isinstance(key.start, (int)) or key.start is None
            int_or_none_stop = isinstance(key.stop, (int)) or key.stop is None
            if int_or_none_start and int_or_none_stop:
                if key.start is not None and key.stop is not None:
                    data = self._ref(skip=key.start, limit=key.stop)
                if key.start is not None and key.stop is None:
                    data = self._ref(skip=key.start)
                if key.start is None and key.stop is not None:
                    data = self._ref(limit=key.stop)
                # both None case handled above
                return data['rows']

        raise RuntimeError("wtf was {0}??".format(key))


    def __iter__(self):
        """
        Implement iteration protocol by calling the
        data method accessor and paging through the responses

        Custom iteration ranges can be controlled via the ctor options

        """
        #TODO custom options need to be converted to couch friendly things
        #     eg if iteration by page is between a start key and end key
        #     verify that paging between startkey/endkey and integer indexes works



