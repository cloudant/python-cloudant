#!/usr/bin/env python
"""
_views_

Utilities for handling design docs and the resulting views they create

"""
from collections import Sequence
import json
import posixpath

from .document import CloudantDocument


class Code(str):
    """
    _Code_

    string derived object that allows us to wrap/manipulate javascript blobs

    """
    def __init__(self, s):
        super(Code, self).__init__(s)


def _codify(code_or_str):
    """
    helper to rationalise None, str or Code objects
    """
    if code_or_str is None:
        return None
    if not isinstance(code_or_str, Code):
        return Code(code_or_str)
    return code_or_str


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


class View(dict):
    """
    Dictionary based object representing a view, exposing the map, reduce
    functions as attributes and supporting query/data access via the view

    """
    def __init__(self, ddoc, view_name, map_func=None, reduce_func=None):
        super(View, self).__init__()
        self.design_doc = ddoc
        self._r_session = self.design_doc._r_session
        self.view_name = view_name
        self[self.view_name] = {}
        self[self.view_name]['map'] = _codify(map_func)
        self[self.view_name]['reduce'] = _codify(reduce_func)

    @property
    def map(self):
        """map property getter"""
        return self[self.view_name]['map']

    @map.setter
    def map(self, js_func):
        """map property setter, accepts str or Code obj"""
        f = _codify(js_func)
        self[self.view_name]['map'] = f

    @property
    def reduce(self):
        """reduce property getter"""
        return self[self.view_name]['reduce']

    @reduce.setter
    def reduce(self, js_func):
        """reduce property setter, accepts str or Code obj"""
        f = _codify(js_func)
        self[self.view_name]['reduce'] = f

    @property
    def url(self):
        return posixpath.join(self.design_doc._document_url, '_view', self.view_name)

    def __getitem__(self, key):
        if key == self.view_name:
            # behave like a normal dict for only dict like key
            return super(View, self).__getitem__(self.view_name)

        if isinstance(key, basestring):
            data = self(key=key)
            return data['rows']

        if isinstance(key, list):
            data = self(key=key)
            return data['rows']

        if isinstance(key, slice):
            # slice is startkey and endkey if str or array
            str_or_none_start = isinstance(key.start, (basestring, list)) or key.start is None
            str_or_none_stop =  isinstance(key.stop, (basestring, list)) or key.stop is None
            if str_or_none_start and str_or_none_stop:
                # startkey/endkey
                data = self(startkey=key.start, endkey=key.stop)
                return data['rows']
            if isinstance(key.start, (int)) and isinstance(key.stop, (int)):
                data = self(skip=key.start, limit=key.stop)
                return data['rows']

        raise RuntimeError("wtf was {0}??".format(key))



    def __call__(self, **kwargs):
        """
        retrieve data from the view, using the kwargs provided
        as query parameters

        descending bool
        endkey string or array
        endkey_docid  string
        group bool
        group_level ??
        include_docs bool
        inclusive_end  bool
        key string
        limit   int
        reduce  boolean
        skip    int
        stale   enum(ok, update_after)
        startkey  string or array
        startkey_docid  string

        """
        for k in kwargs:
            if k not in ALL_ARGS:
                raise ValueError("Invalid argument: {0}".format(k))
        params = python_to_couch(kwargs)
        resp = self._r_session.get(self.url, params=params)
        resp.raise_for_status()
        return resp.json()


class DesignDocument(CloudantDocument):
    """
    _DesignDocument_

    Specialisation of a document to be a design doc containing
    the various views, shows, lists etc.

    """
    def __init__(self, cloudant_database, document_id=None):
        super(DesignDocument, self).__init__(cloudant_database, document_id)

    @property
    def views(self):
        """accessor property for views dictionary"""
        return self['views']

    def add_view(self, view_name, map_func, reduce_func=None):
        """
        _add_view_

        Add a new view to this design document, given a map function
        and optional reduce function.

        :param view_name: Name of the view
        :param map_func: str or Code object containing js map function
        :param reduce_func: str or Code object containing js reduce function
        """
        v = View(self, view_name, map_func, reduce_func)
        self.views[view_name] = v
        self.save()

    def fetch(self):
        """
        _fetch_

        Grab the remote document and populate build the View structure

        """
        super(DesignDocument, self).fetch()
        for view_name, view_def in self.get('views', {}).iteritems():
            self['views'][view_name] = View(
                self,
                view_name,
                view_def.get('map'),
                view_def.get('reduce')
            )

    def iterviews(self):
        """
        _iterviews_

        Iterate over the view name, view instance

        """
        for view_name, view in self.views.iteritems():
            yield view_name, view

    def list_views(self):
        """
        _views_

        return a list of available views on this design doc
        """
        return self.views.keys()

    def get_view(self, view_name):
        """
        _get_view_

        Get a specific view by name.

        """
        return self.views.get(view_name)

    def info(self):
        """
        retrieve the view info data, returns dictionary

        GET databasename/_design/test/_info
        """
        pass

    def cleanup(self):
        """

        POST /some_database/_view_cleanup

        """
        pass

    def compact(self):
        """
        POST /some_database/_compact/designname
        """
        pass