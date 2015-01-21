#!/usr/bin/env python
"""
_views_

Utilities for handling design docs and the resulting views they create

"""
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


class View(dict):
    """
    Dictionary based object representing a view, exposing the map, reduce
    functions as attributes and supporting query/data access via the view

    """
    def __init__(self, ddoc, view_name, map_func=None, reduce_func=None):
        super(View, self).__init__()
        self.design_doc = ddoc
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
        # TODO - save doc to db

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
