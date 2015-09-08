#!/usr/bin/env python
"""
_views_

Utilities for handling design docs and the resulting views they create

"""
import contextlib
import posixpath

from .document import Document
from .result import Result, python_to_couch


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

    Provides a sliceable and iterable default result collection that can 
    be used to query the view data via the result attribute.

    Eg:

    Using integers to skip/limit:
    view.result[100:200]
    view.result[:200]
    view.result[100:]

    Using strings or lists as startkey/endkey:

    view.result[ ["2013","10"]:["2013","11"] ]
    view.result[["2013","10"]]
    view.result[["2013","10"]:]

    For large views, iteration is supported via result:

    for doc in view.result:
        print doc

    The default result collection provides basic functionality, 
    which can be customised with other arguments to the view URL 
    using the custom_result context.

    For example:

    #including documents
    with view.custom_result(include_docs=True) as rslt:
        rslt[100:200] # slice by result
        rslt[["2013","10"]:["2013","11"]] # slice by startkey/endkey

        #iteration
        for doc in rslt:
            print doc

    Iteration over a view within startkey/endkey range:

    with view.custom_result(startkey="2013", endkey="2014") as rslt:
        for doc in rslt:
            print doc

    """
    def __init__(self, ddoc, view_name, map_func=None, reduce_func=None):
        super(View, self).__init__()
        self.design_doc = ddoc
        self._r_session = self.design_doc._r_session
        self.view_name = view_name
        self[self.view_name] = {}
        self[self.view_name]['map'] = _codify(map_func)
        self[self.view_name]['reduce'] = _codify(reduce_func)
        self.result = Result(self)

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
        """property that builds the view URL"""
        return posixpath.join(
            self.design_doc._document_url,
            '_view',
            self.view_name
        )

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
        params = python_to_couch(kwargs)
        resp = self._r_session.get(self.url, params=params)
        resp.raise_for_status()
        return resp.json()

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        _custom_result_

        If you want to customise the result behaviour,
        you can build your own with extra options to the result
        call using this context manager.

        Example:

        with view.custom_result(include_docs=True, reduce=False) as rslt:
            data = rslt[100:200]

        """
        rslt = Result(self, **options)
        yield rslt
        del rslt


class DesignDocument(Document):
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
        raise NotImplemented("info not yet implemented")

    def cleanup(self):
        """

        POST /some_database/_view_cleanup

        """
        raise NotImplemented("cleanup not yet implemented")

    def compact(self):
        """
        POST /some_database/_compact/designname
        """
        raise NotImplemented("compact not yet implemented")
