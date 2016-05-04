#!/usr/bin/env python
# Copyright (c) 2015 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
API module/class for interacting with a design document in a database.
"""
from cloudant.search import SearchIndex
from ._2to3 import iteritems_
from .document import Document
from .view import View, QueryIndexView
from .error import CloudantArgumentError, CloudantException
from ._common_util import QUERY_LANGUAGE

class DesignDocument(Document):
    """
    Encapsulates a specialized version of a
    :class:`~cloudant.document.Document`.  A DesignDocument object is
    instantiated with a reference to a database and
    provides an API to view management, search index management, list and show
    functions, etc.  When instantiating a DesignDocument or
    when setting the document id (``_id``) field, the value must start with
    ``_design/``.  If it does not, then ``_design/`` will be prepended to
    the provided document id value.

    :param database: A database instance used by the DesignDocument.  Can be
        either a ``CouchDatabase`` or ``CloudantDatabase`` instance.
    :param str document_id: Optional document id.  If provided and does not
        start with ``_design/``, it will be prepended with ``_design/``.
    """
    def __init__(self, database, document_id=None):
        if document_id and not document_id.startswith('_design/'):
            document_id = '_design/{0}'.format(document_id)
        super(DesignDocument, self).__init__(database, document_id)
        self.setdefault('views', dict())
        self.setdefault('indexes', dict())

    @property
    def views(self):
        """
        Provides an accessor property to the View dictionary in the locally
        cached DesignDocument.

        :returns: Dictionary containing view names and View objects as key/value
        """
        return self.get('views')

    @property
    def search_indexes(self):
        """
        Provides an accessor property to the SearchIndex dictionary in the
        locally cached DesignDocument.

        :returns: Dictionary containing search index names and objects
            as key/value
        """
        return self.get('indexes')

    def add_view(self, view_name, map_func, reduce_func=None, **kwargs):
        """
        Appends a MapReduce view to the locally cached DesignDocument View
        dictionary.  To create a JSON query index use
        :func:`~cloudant.database.CloudantDatabase.create_query_index` instead.
        A CloudantException is raised if an attempt to add a QueryIndexView
        (JSON query index) using this method is made.

        :param str view_name: Name used to identify the View.
        :param str map_func: Javascript map function.
        :param str reduce_func: Optional Javascript reduce function.
        """
        if self.get_view(view_name) is not None:
            msg = "View {0} already exists in this design doc".format(view_name)
            raise CloudantArgumentError(msg)
        if self.get('language', None) == QUERY_LANGUAGE:
            msg = ('Cannot add a MapReduce view to a '
                   'design document for query indexes.')
            raise CloudantException(msg)

        view = View(self, view_name, map_func, reduce_func, **kwargs)
        self.views.__setitem__(view_name, view)

    def add_search_index(self, search_index_name, search_index, **kwargs):
        """
        Appends a Cloudant search index to the locally cached DesignDocument
        SearchIndex dictionary.

        :param str search_index_name: Name used to identify the SearchIndex.
        :param str search_index: Javascript search index function.
        """
        if self.get_search_index(search_index_name) is not None:
            msg = "Search index {0} already exists in this design doc"\
                .format(search_index_name)
            raise CloudantArgumentError(msg)

        search = SearchIndex(self, search_index_name, search_index, **kwargs)
        self.search_indexes.__setitem__(search_index_name, search)

    def update_view(self, view_name, map_func, reduce_func=None, **kwargs):
        """
        Modifies/overwrites an existing MapReduce view definition in the
        locally cached DesignDocument View dictionary.  To update a JSON
        query index use
        :func:`~cloudant.database.CloudantDatabase.delete_query_index` followed
        by :func:`~cloudant.database.CloudantDatabase.create_query_index`
        instead.  A CloudantException is raised if an attempt to update a
        QueryIndexView (JSON query index) using this method is made.

        :param str view_name: Name used to identify the View.
        :param str map_func: Javascript map function.
        :param str reduce_func: Optional Javascript reduce function.
        """
        view = self.get_view(view_name)
        if view is None:
            msg = "View {0} does not exist in this design doc".format(view_name)
            raise CloudantArgumentError(msg)
        if isinstance(view, QueryIndexView):
            msg = 'Cannot update a query index view using this method.'
            raise CloudantException(msg)

        view = View(self, view_name, map_func, reduce_func, **kwargs)
        self.views.__setitem__(view_name, view)

    def update_search_index(self, search_index_name, search_index, **kwargs):
        """
        Modifies/overwrites an existing Cloudant search index in the
        locally cached DesignDocument SearchIndex dictionary.

        :param str search_index_name: Name used to identify the SearchIndex.
        :param str search_index: Javascript search index function.
        """
        search = self.get_search_index(search_index_name)
        if search is None:
            msg = "Search index {0} does not exist in this design doc"\
                .format(search_index_name)
            raise CloudantArgumentError(msg)

        search = SearchIndex(self, search_index_name, search_index, **kwargs)
        self.search_indexes.__setitem__(search_index_name, search)

    def delete_view(self, view_name):
        """
        Removes an existing MapReduce view definition from the locally cached
        DesignDocument View dictionary.  To delete a JSON query index
        use :func:`~cloudant.database.CloudantDatabase.delete_query_index`
        instead.  A CloudantException is raised if an attempt to delete a
        QueryIndexView (JSON query index) using this method is made.

        :param str view_name: Name used to identify the View.
        """
        view = self.get_view(view_name)
        if view is None:
            return
        if isinstance(view, QueryIndexView):
            msg = 'Cannot delete a query index view using this method.'
            raise CloudantException(msg)

        self.views.__delitem__(view_name)

    def delete_search_index(self, search_index_name):
        """
        Removes an existing Cloudant search index in the locally cached
        DesignDocument SearchIndex dictionary.

        :param str search_index_name: Name used to identify the Search index.
        """
        search_index = self.get_search_index(search_index_name)
        if search_index is None:
            return

        self.search_indexes.__delitem__(search_index_name)

    def fetch(self):
        """
        Retrieves the remote design document content and populates the locally
        cached DesignDocument dictionary.  View content is stored either as
        View or QueryIndexView objects which are extensions of the ``dict``
        type.  All other design document data are stored directly as
        ``dict`` types.
        """
        super(DesignDocument, self).fetch()
        if not self.views:
            # Ensure views dict exists in locally cached DesignDocument.
            self.setdefault('views', dict())
        else:
            for view_name, view_def in iteritems_(self.get('views', dict())):
                if self.get('language', None) != QUERY_LANGUAGE:
                    self['views'][view_name] = View(
                        self,
                        view_name,
                        view_def.pop('map', None),
                        view_def.pop('reduce', None),
                        **view_def
                    )
                else:
                    self['views'][view_name] = QueryIndexView(
                        self,
                        view_name,
                        view_def.pop('map', None),
                        view_def.pop('reduce', None),
                        **view_def
                    )
        if not self.search_indexes:
            # Ensure indexes dict exists in locally cached DesignDocument.
            self.setdefault('indexes', dict())
        if self.search_indexes:
            for (search_index_name, search_index) \
                    in iteritems_(self.get('indexes', dict())):
                self['indexes'][search_index_name] = SearchIndex(
                    self,
                    search_index_name,
                    search_index,
                    **search_index
                )

    def save(self):
        """
        Saves changes made to the locally cached DesignDocument object's data
        structures to the remote database.  If the design document does not
        exist remotely then it is created in the remote database.  If the object
        does exist remotely then the design document is updated remotely.  In
        either case the locally cached DesignDocument object is also updated
        accordingly based on the successful response of the operation.
        """
        if self.views:
            if self.get('language', None) != QUERY_LANGUAGE:
                for view_name, view in self.iterviews():
                    if isinstance(view, QueryIndexView):
                        msg = 'View {0} must be of type View.'.format(view_name)
                        raise CloudantException(msg)
            else:
                for view_name, view in self.iterviews():
                    if not isinstance(view, QueryIndexView):
                        msg = (
                            'View {0} must be of type QueryIndexView.'
                        ).format(view_name)
                        raise CloudantException(msg)
        else:
            # Ensure empty views dict is not saved remotely.
            self.__delitem__('views')

        if not self.search_indexes:
            # Ensure empty indexes dict is not saved remotely.
            self.__delitem__('indexes')

        super(DesignDocument, self).save()

        if not self.views:
            # Ensure views dict exists in locally cached DesignDocument.
            self.setdefault('views', dict())
        if not self.search_indexes:
            # Ensure indexes dict exists in locally cached DesignDocument.
            self.setdefault('indexes', dict())

    def __setitem__(self, key, value):
        """
        Ensures that when setting the document id for a DesignDocument it is
        always prefaced with '_design'.
        """
        if (
                key == '_id' and
                value is not None and
                not value.startswith('_design/')
        ):
            value = '_design/{0}'.format(value)
        super(DesignDocument, self).__setitem__(key, value)

    def iterviews(self):
        """
        Provides a way to iterate over the locally cached DesignDocument View
        dictionary.

        For example:

        .. code-block:: python

            for view_name, view in ddoc.iterviews():
                # Perform view processing

        :returns: Iterable containing view name and associated View object
        """
        for view_name, view in iteritems_(self.views):
            yield view_name, view

    def itersearchindexes(self):
        """
        Provides a way to iterate over the locally cached DesignDocument
        SearchIndex dictionary.

        For example:

        .. code-block:: python

            for search_index_name, search_index in ddoc.itersearchindexes():
                # Perform search index processing

        :returns: Iterable containing search index name and associated
        SearchIndex object
        """
        for search_index_name, search_index in iteritems_(self.search_indexes):
            yield search_index_name, search_index

    def list_views(self):
        """
        Retrieves a list of available View objects in the locally cached
        DesignDocument.

        :returns: List of view names
        """
        return list(self.views.keys())

    def list_search_indexes(self):
        """
        Retrieves a list of available SearchIndex objects in the locally cached
        DesignDocument.

        :returns: List of search index names
        """
        return list(self.search_indexes.keys())

    def get_view(self, view_name):
        """
        Retrieves a specific View from the locally cached DesignDocument by
        name.

        :param str view_name: Name used to identify the View.

        :returns: View object for the specified view_name
        """
        return self.views.get(view_name)

    def get_search_index(self, search_index_name):
        """
        Retrieves a specific SearchIndex from the locally cached DesignDocument
        by name.

        :param str search_index_name: Name used to identify the SearchIndex.

        :returns: SearchIndex object for the specified search_index_name
        """
        return self.search_indexes.get(search_index_name)

    def info(self):
        """
        Retrieves the design document view information data, returns dictionary

        GET databasename/_design/{ddoc}/_info
        """
        raise NotImplementedError("_info not yet implemented")
