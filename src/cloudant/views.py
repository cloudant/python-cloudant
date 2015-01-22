#!/usr/bin/env python
"""
_views_

Utilities for handling design docs and the resulting views they create

"""
import contextlib
import posixpath

from .document import CloudantDocument
from .index import Index, ALL_ARGS, python_to_couch


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
        self.index = Index(self)

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

    @contextlib.contextmanager
    def custom_index(self, **options):
        indx = Index(self, **options)
        yield indx
        del indx


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