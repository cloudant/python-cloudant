#!/usr/bin/env python
"""
_design_document_

Class representing a Cloudant design document

"""
from .document import Document
from .views import View
from .errors import CloudantArgumentError


class DesignDocument(Document):
    """
    _DesignDocument_

    Specialisation of a document to be a design doc containing
    the various views, shows, lists etc.

    """
    def __init__(self, cloudant_database, document_id=None):
        super(DesignDocument, self).__init__(cloudant_database, document_id)
        self.setdefault('views', {})

    @property
    def views(self):
        """accessor property for views dictionary"""
        return self.get('views')

    def add_view(self, view_name, map_func, reduce_func=None):
        """
        _add_view_

        Add a new view to this design document, given a map function
        and optional reduce function.

        :param view_name: Name of the view
        :param map_func: str or Code object containing js map function
        :param reduce_func: str or Code object containing js reduce function
        """
        if self.get_view(view_name) is not None:
            msg = "View {0} already exists in this design doc".format(view_name)
            raise CloudantArgumentError(msg)
        v = View(self, view_name, map_func, reduce_func)
        self.views[view_name] = v
        self.save()

    def update_view(self, view_name, map_func, reduce_func=None):
        """
        _update_view_

        Modify an existing view on this design document, given a map function
        and optional reduce function.

        :param view_name: Name of the view
        :param map_func: str or Code object containing js map function
        :param reduce_func: str or Code object containing js reduce function
        """
        v = self.get_view(view_name)
        if v is None:
            msg = "View {0} does not exist in this design doc".format(view_name)
            raise CloudantArgumentError(msg)
        v.map = map_func
        if reduce_func is not None:
            v.reduce = reduce_func
        self.views[view_name] = v
        self.save()

    def delete_view(self, view_name):
        """
        _delete_view_

        Remove a view from this design document.

        :param view_name: Name of the view
        """
        if self.get_view(view_name) is not None:
            del self.views[view_name]
            self.save()

    def fetch(self):
        """
        _fetch_

        Grab the remote document and populate the View structure.
        Other structures to follow...

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
