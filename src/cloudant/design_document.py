#!/usr/bin/env python
# Copyright (C) 2015, 2019 IBM. All rights reserved.
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
from ._2to3 import iteritems_, url_quote_plus, STRTYPE
from ._common_util import QUERY_LANGUAGE, codify, response_to_json_dict
from .document import Document
from .view import View, QueryIndexView
from .error import CloudantArgumentError, CloudantDesignDocumentException

class DesignDocument(Document):
    """
    Encapsulates a specialized version of a
    :class:`~cloudant.document.Document`.  A DesignDocument object is
    instantiated with a reference to a database and
    provides an API to view management, index management, list and show
    functions, etc.  When instantiating a DesignDocument or
    when setting the document id (``_id``) field, the value must start with
    ``_design/``.  If it does not, then ``_design/`` will be prepended to
    the provided document id value.

    Note:  Currently only the view management and search index management API
    exists.  Remaining design document functionality will be added later.

    :param database: A database instance used by the DesignDocument.  Can be
        either a ``CouchDatabase`` or ``CloudantDatabase`` instance.
    :param str document_id: Optional document id.  If provided and does not
        start with ``_design/``, it will be prepended with ``_design/``.
    :param bool partitioned: Optional. Create as a partitioned design document.
        Defaults to ``False`` for both partitioned and non-partitioned
        databases.
    """
    def __init__(self, database, document_id=None, partitioned=False):
        if document_id and not document_id.startswith('_design/'):
            document_id = '_design/{0}'.format(document_id)
        super(DesignDocument, self).__init__(database, document_id)

        if partitioned:
            self.setdefault('options', {'partitioned': True})
        else:
            self.setdefault('options', {'partitioned': False})

        self._nested_object_names = frozenset(['views', 'indexes', 'lists', 'shows'])
        for prop in self._nested_object_names:
            self.setdefault(prop, dict())

    @property
    def validate_doc_update(self):
        """
        Provides an accessor property to the update validators dictionary in
        the locally cached DesignDocument.  Update validators evaluate whether a
        document should be written to disk when insertions and updates are attempted.

        Update validator example:

        .. code-block:: python

            # Add the update validator to ``validate_doc_update`` and save the design document
            ddoc = DesignDocument(self.db, '_design/ddoc001')
            ddoc['validate_doc_update'] = (
                'function(newDoc, oldDoc, userCtx, secObj) { '
                'if (newDoc.address === undefined) { '
                'throw({forbidden: \'Document must have an address.\'}); }}')
            ddoc.save()

        For more details, see the `Update Validators documentation
        <https://console.bluemix.net/docs/services/Cloudant/api/design_documents.html#update-validators>`_.

        :returns: Dictionary containing update validator functions
        """
        return self.get('validate_doc_update')

    @property
    def filters(self):
        """
        Provides an accessor property to the filters dictionary in the locally cached
        DesignDocument.  Filter functions enable you to add tests for filtering each
        of the objects included in the changes feed.  If any of the function tests
        fail, the object is filtered from the feed.  If the function returns a true
        result when applied to a change, the change remains in the feed.

        Filter functions require two arguments: ``doc`` and ``req``.  The ``doc`` argument
        represents the document being tested for filtering.  The ``req`` argument contains
        additional information about the HTTP request.

        Filter function example:

        .. code-block:: python

            # Add the filter function to ``filters`` and save the design document
            ddoc = DesignDocument(self.db, '_design/ddoc001')
            # Filter and remove documents that are not of ``type`` mail
            ddoc['filters'] = {
                'filter001': 'function(doc, req){if (doc.type != \'mail\'){return false;} '
                             'return true;} '
            }
            ddoc.save()

        To execute filter functions on a changes feed, see the database API
        :func:`~cloudant.database.CouchDatabase.changes`

        For more details, see the `Filter functions documentation
        <https://console.bluemix.net/docs/services/Cloudant/api/design_documents.html#filter-functions>`_.

        :returns: Dictionary containing filter function names and functions
            as key/value
        """
        return self.get('filters')

    @property
    def updates(self):
        """
        Provides an accessor property to the updates dictionary in the locally
        cached DesignDocument. Update handlers are custom functions stored on
        Cloudant's server that will create or update a document.
        To execute the update handler function, see
        :func:`~cloudant.database.CouchDatabase.update_handler_result`.

        Update handlers receive two arguments: ``doc`` and ``req``. If a document ID is
        provided in the request to the update handler, then ``doc`` will be the
        document corresponding with that ID.
        If no ID was provided, ``doc`` will be null.

        Update handler example:

        .. code-block:: python

            # Add the update handler to ``updates`` and save the design document
            ddoc = DesignDocument(self.db, '_design/ddoc001')
            ddoc001['updates'] = {
                'update001': 'function(doc, req) { if (!doc) '
                             '{ if ('id' in req && req.id){ return [{_id: req.id}, '
                             '\"New World\"] } return [null, \"Empty World\"] } '
                             'doc.world = \'hello\'; '
                             'return [doc, \"Added world.hello!\"]} '
            }
            ddoc.save()

        Note: Update handler functions must return an array of two elements,
        the first being the document to save (or null, if you don't want to
        save anything), and the second being the response body.

        :returns: Dictionary containing update handler names and objects
            as key/value
        """
        return self.get('updates')

    @property
    def st_indexes(self):
        """
        Provides an accessor property to the Cloudant Geospatial
        (a.k.a. Cloudant Geo) indexes dictionary in the locally cached
        DesignDocument.  Each Cloudant Geo index is a JSON object within the
        ``st_indexes`` containing an index name and a javascript function.

        Note: To make it easier to work with Cloudant Geo documents, it is best
        practice to create a separate design document specifically for
        Cloudant Geo indexes.

        Geospatial index example:

        .. code-block:: python

            # Add the Cloudant Geo index to ``st_indexes`` and save the design document
            ddoc = DesignDocument(self.db, '_design/ddoc001')
            ddoc['st_indexes'] = {
                'geoidx': {
                    'index': 'function(doc) { '
                             'if (doc.geometry && doc.geometry.coordinates) { '
                             'st_index(doc.geometry);}} '
                }
            }
            ddoc.save()

        Once the Cloudant Geo index is saved to the remote database, you can
        query the index with a GET request.  To issue a request against the
        ``_geo`` endpoint, see the steps outlined in the `endpoint access
        <getting_started.html#endpoint-access>`_ section.

        For more details, see the `Cloudant Geospatial
        documentation <https://console.bluemix.net/docs/services/Cloudant/api/cloudant-geo.html>`_.

        :return: Dictionary containing Cloudant Geo names and index objects
            as key/value
        """
        return self.get('st_indexes')

    @property
    def lists(self):
        """
        Provides an accessor property to the lists dictionary in the locally
        cached DesignDocument.

        :returns: Dictionary containing list names and objects as key/value
        """
        return self.get('lists')

    @property
    def shows(self):
        """
        Provides an accessor property to the shows dictionary in the
        locally cached DesignDocument.

        :returns: Dictionary containing show names and functions
            as key/value
        """
        return self.get('shows')

    @property
    def rewrites(self):
        """
        Provides an accessor property to a list of dictionaries with rewrite
        rules in the locally cached DesignDocument.  Each rule for URL rewriting
        is a JSON object with four fields: ``from``, ``to``, ``method``,
        and ``query``.

        Note: Requests that match the rewrite rules must have a URL path that
        starts with ``/$DATABASE/_design/doc/_rewrite``.

        Rewrite rule example:

        .. code-block:: python

            # Add the rule to ``rewrites`` and save the design document
            ddoc = DesignDocument(self.db, '_design/ddoc001')
            ddoc['rewrites'] = [
                {"from": "/old/topic",
                 "to": "/new/",
                 "method": "GET",
                 "query": {}
                 }
            ]
            ddoc.save()

        Once the rewrite rule is saved to the remote database, the GET
        request URL ``/$DATABASE/_design/doc/_rewrite/old/topic?k=v`` would be
        rewritten as ``/$DATABASE/_design/doc/_rewrite/new?k=v``.

        For more details on URL rewriting, see the `rewrite rules
        documentation <https://console.bluemix.net/docs/services/Cloudant/api/design_documents.html
        #rewrite-rules>`_.

        :returns: List of dictionaries containing rewrite rules as key/value
        """
        return self.get('rewrites')

    @property
    def views(self):
        """
        Provides an accessor property to the View dictionary in the locally
        cached DesignDocument.

        :returns: Dictionary containing view names and View objects as key/value
        """
        return self.get('views')

    @property
    def indexes(self):
        """
        Provides an accessor property to the indexes dictionary in the
        locally cached DesignDocument.

        :returns: Dictionary containing index names and index objects
            as key/value
        """
        return self.get('indexes')

    def document_partition_url(self, partition_key):
        """
        Retrieve the design document partition URL.

        :param str partition_key: Partition key.
        :return: Design document partition URL.
        :rtype: str
        """
        return '/'.join((
            self._database.database_partition_url(partition_key),
            '_design',
            url_quote_plus(self['_id'][8:], safe='')
        ))

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
            raise CloudantArgumentError(107, view_name)
        if self.get('language', None) == QUERY_LANGUAGE:
            raise CloudantDesignDocumentException(101)

        view = View(self, view_name, map_func, reduce_func, **kwargs)
        self.views.__setitem__(view_name, view)

    def add_search_index(self, index_name, search_func, analyzer=None):
        """
        Appends a Cloudant search index to the locally cached DesignDocument
        indexes dictionary.

        :param str index_name: Name used to identify the search index.
        :param str search_func: Javascript search index function.
        :param analyzer: Optional analyzer for this search index.
        """
        if self.get_index(index_name) is not None:
            raise CloudantArgumentError(108, index_name)
        if analyzer is not None:
            search = {'index': codify(search_func), 'analyzer': analyzer}
        else:
            search = {'index': codify(search_func)}

        self.indexes.__setitem__(index_name, search)

    def add_list_function(self, list_name, list_func):
        """
        Appends a list function to the locally cached DesignDocument
        indexes dictionary.

        :param str list_name: Name used to identify the list function.
        :param str list_func: Javascript list function.
        """
        if self.get_list_function(list_name) is not None:
            raise CloudantArgumentError(109, list_name)

        self.lists.__setitem__(list_name, codify(list_func))

    def add_show_function(self, show_name, show_func):
        """
        Appends a show function to the locally cached DesignDocument
        shows dictionary.

        :param show_name: Name used to identify the show function.
        :param show_func: Javascript show function.
        """
        if self.get_show_function(show_name) is not None:
            raise CloudantArgumentError(110, show_name)

        self.shows.__setitem__(show_name, show_func)

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
            raise CloudantArgumentError(111, view_name)
        if isinstance(view, QueryIndexView):
            raise CloudantDesignDocumentException(102)

        view = View(self, view_name, map_func, reduce_func, **kwargs)
        self.views.__setitem__(view_name, view)

    def update_search_index(self, index_name, search_func, analyzer=None):
        """
        Modifies/overwrites an existing Cloudant search index in the
        locally cached DesignDocument indexes dictionary.

        :param str index_name: Name used to identify the search index.
        :param str search_func: Javascript search index function.
        :param analyzer: Optional analyzer for this search index.
        """
        search = self.get_index(index_name)
        if search is None:
            raise CloudantArgumentError(112, index_name)
        if analyzer is not None:
            search = {'index': codify(search_func), 'analyzer': analyzer}
        else:
            search = {'index': codify(search_func)}

        self.indexes.__setitem__(index_name, search)

    def update_list_function(self, list_name, list_func):
        """
        Modifies/overwrites an existing list function in the
        locally cached DesignDocument indexes dictionary.

        :param str list_name: Name used to identify the list function.
        :param str list_func: Javascript list function.
        """
        if self.get_list_function(list_name) is None:
            raise CloudantArgumentError(113, list_name)

        self.lists.__setitem__(list_name, codify(list_func))

    def update_show_function(self, show_name, show_func):
        """
        Modifies/overwrites an existing show function in the
        locally cached DesignDocument shows dictionary.

        :param show_name: Name used to identify the show function.
        :param show_func: Javascript show function.
        """
        if self.get_show_function(show_name) is None:
            raise CloudantArgumentError(114, show_name)

        self.shows.__setitem__(show_name, show_func)

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
            raise CloudantDesignDocumentException(103)

        self.views.__delitem__(view_name)

    def delete_index(self, index_name):
        """
        Removes an existing index in the locally cached DesignDocument
        indexes dictionary.

        :param str index_name: Name used to identify the index.
        """
        index = self.get_index(index_name)
        if index is None:
            return

        self.indexes.__delitem__(index_name)

    def delete_list_function(self, list_name):
        """
        Removes an existing list function in the locally cached DesignDocument
        lists dictionary.

        :param str list_name: Name used to identify the list.
        """
        self.lists.__delitem__(list_name)

    def delete_show_function(self, show_name):
        """
        Removes an existing show function in the locally cached DesignDocument
        shows dictionary.

        :param show_name: Name used to identify the list.
        """
        if self.get_show_function(show_name) is None:
            return

        self.shows.__delitem__(show_name)

    def fetch(self):
        """
        Retrieves the remote design document content and populates the locally
        cached DesignDocument dictionary.  View content is stored either as
        View or QueryIndexView objects which are extensions of the ``dict``
        type.  All other design document data are stored directly as
        ``dict`` types.
        """
        super(DesignDocument, self).fetch()
        if self.views:
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

        for prop in self._nested_object_names:
            # Ensure dict for each sub-object exists in locally cached DesignDocument.
            getattr(self, prop, self.setdefault(prop, dict()))

    # pylint: disable=too-many-branches
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
                        raise CloudantDesignDocumentException(104, view_name)
            else:
                for view_name, view in self.iterviews():
                    if not isinstance(view, QueryIndexView):
                        raise CloudantDesignDocumentException(105, view_name)

        if self.indexes:
            if self.get('language', None) != QUERY_LANGUAGE:
                for index_name, search in self.iterindexes():
                    # Check the instance of the javascript search function
                    if not isinstance(search['index'], STRTYPE):
                        raise CloudantDesignDocumentException(106, index_name)
            else:
                for index_name, index in self.iterindexes():
                    if not isinstance(index['index'], dict):
                        raise CloudantDesignDocumentException(107, index_name)

        for prop in self._nested_object_names:
            if not getattr(self, prop):
                # Ensure empty dict for each sub-object is not saved remotely.
                self.__delitem__(prop)

        super(DesignDocument, self).save()

        for prop in self._nested_object_names:
            # Ensure views, indexes, and lists dict exist in locally cached DesignDocument.
            getattr(self, prop, self.setdefault(prop, dict()))

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

    def iterindexes(self):
        """
        Provides a way to iterate over the locally cached DesignDocument
        indexes dictionary.

        For example:

        .. code-block:: python

            for index_name, search_func in ddoc.iterindexes():
                # Perform search index processing

        :returns: Iterable containing index name and associated
            index object
        """
        for index_name, search_func in iteritems_(self.indexes):
            yield index_name, search_func

    def iterlists(self):
        """
        Provides a way to iterate over the locally cached DesignDocument
        lists dictionary.

        :returns: Iterable containing list function name and associated
            list function
        """
        for list_name, list_func in iteritems_(self.lists):
            yield list_name, list_func

    def itershows(self):
        """
        Provides a way to iterate over the locally cached DesignDocument
        shows dictionary.

        :returns: Iterable containing show function name and associated
            show function
        """
        for show_name, show_func in iteritems_(self.shows):
            yield show_name, show_func

    def list_views(self):
        """
        Retrieves a list of available View objects in the locally cached
        DesignDocument.

        :returns: List of view names
        """
        return list(self.views.keys())

    def list_indexes(self):
        """
        Retrieves a list of available indexes in the locally cached
        DesignDocument.

        :returns: List of index names
        """
        return list(self.indexes.keys())

    def list_list_functions(self):
        """
        Retrieves a list of available list functions in the locally cached
        DesignDocument lists dictionary.

        :returns: List of list function names
        """
        return list(self.lists.keys())

    def list_show_functions(self):
        """
        Retrieves a list of available show functions in the locally cached
        DesignDocument shows dictionary.

        :returns: List of show function names
        """
        return list(self.shows.keys())

    def get_view(self, view_name):
        """
        Retrieves a specific View from the locally cached DesignDocument by
        name.

        :param str view_name: Name used to identify the View.

        :returns: View object for the specified view_name
        """
        return self.views.get(view_name)

    def get_index(self, index_name):
        """
        Retrieves a specific index from the locally cached DesignDocument
        indexes dictionary by name.

        :param str index_name: Name used to identify the index.

        :returns: Index dictionary for the specified index name
        """
        return self.indexes.get(index_name)

    def get_list_function(self, list_name):
        """
        Retrieves a specific list function from the locally cached DesignDocument
        lists dictionary by name.

        :param str list_name: Name used to identify the list function.

        :returns: String form of the specified list function
        """
        return self.lists.get(list_name)

    def get_show_function(self, show_name):
        """
        Retrieves a specific show function from the locally cached DesignDocument
        shows dictionary by name.

        :param str show_name: Name used to identify the show function.

        :returns: String form of the specified show function
        """
        return self.shows.get(show_name)

    def info(self):
        """
        Retrieves the design document view information data, returns dictionary

        GET databasename/_design/{ddoc}/_info
        """
        ddoc_info = self.r_session.get(
            '/'.join([self.document_url, '_info']))
        ddoc_info.raise_for_status()
        return response_to_json_dict(ddoc_info)

    def search_info(self, search_index):
        """
        Retrieves information about a specified search index within the design
        document, returns dictionary

        GET databasename/_design/{ddoc}/_search_info/{search_index}
        """
        ddoc_search_info = self.r_session.get(
            '/'.join([self.document_url, '_search_info', search_index]))
        ddoc_search_info.raise_for_status()
        return response_to_json_dict(ddoc_search_info)

    def search_disk_size(self, search_index):
        """
        Retrieves disk size information about a specified search index within
        the design document, returns dictionary

        GET databasename/_design/{ddoc}/_search_disk_size/{search_index}
        """
        ddoc_search_disk_size = self.r_session.get(
            '/'.join([self.document_url, '_search_disk_size', search_index]))
        ddoc_search_disk_size.raise_for_status()
        return response_to_json_dict(ddoc_search_disk_size)
