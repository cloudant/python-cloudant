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
from .document import Document
from .views import View, QueryIndexView
from .errors import CloudantArgumentError, CloudantException

QUERY_LANGUAGE = 'query'

class DesignDocument(Document):
    """
    Encapsulates a specialized version of a
    :class:`~cloudant.document.Document`.  A DesignDocument object is
    instantiated with a reference to a database and
    provides an API to view management, list and show
    functions, search indexes, etc.  When instantiating a DesignDocument or
    when setting the document id (``_id``) field, the value must start with
    ``_design/``.  If it does not, then ``_design/`` will be prepended to
    the provided document id value.

    Note:  Currently only the view management API exists.  Remaining design
    document functionality will be added later.

    :param database: A database instance used by the DesignDocument.  Can be
        either a ``CouchDatabase`` or ``CloudantDatabase`` instance.
    :param str document_id: Optional document id.  If provided and does not
        start with ``_design/``, it will be prepended with ``_design/``.
    """
    def __init__(self, database, document_id=None):
        if document_id and not document_id.startswith('_design/'):
            document_id = '_design/{0}'.format(document_id)
        super(DesignDocument, self).__init__(database, document_id)
        self.setdefault('views', {})

    @property
    def views(self):
        """
        Provides an accessor property to the View dictionary in the locally
        cached DesignDocument.

        :returns: Dictionary containing view names and View objects as key/value
        """
        return self.get('views')

    def add_view(self, view_name, map_func, reduce_func=None, **kwargs):
        """
        Appends a MapReduce view to the locally cached DesignDocument View
        dictionary.  To create a query index use
        :func:`~cloudant.database.CloudantDatabase.create_index` instead.  A
        CloudantException is raised if an attempt to add a QueryIndexView
        (query index) using this method is made.

        :param str view_name: Name used to identify the View.
        :param str map_func: Javascript map function.  Can also be a
            :class:`~cloudant.views.Code` object.
        :param str reduce_func: Optional Javascript reduce function.
            Can also be a :class:`~cloudant.views.Code` object.
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

    def update_view(self, view_name, map_func, reduce_func=None, **kwargs):
        """
        Modifies/overwrites an existing MapReduce view definition in the
        locally cached DesignDocument View dictionary.  To update a query index
        use :func:`~cloudant.database.CloudantDatabase.delete_index` followed by
        :func:`~cloudant.database.CloudantDatabase.create_index` instead.  A
        CloudantException is raised if an attempt to update a QueryIndexView
        (query index) using this method is made.

        :param str view_name: Name used to identify the View.
        :param str map_func: Javascript map function.  Can also be a
            :class:`~cloudant.views.Code` object.
        :param str reduce_func: Optional Javascript reduce function.
            Can also be a :class:`~cloudant.views.Code` object.
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

    def delete_view(self, view_name):
        """
        Removes an existing MapReduce view definition from the locally cached
        DesignDocument View dictionary.  To delete a query index use
        :func:`~cloudant.database.CloudantDatabase.delete_index` instead.  A
        CloudantException is raised if an attempt to delete a QueryIndexView
        (query index) using this method is made.

        :param str view_name: Name used to identify the View.
        """
        view = self.get_view(view_name)
        if view is None:
            return
        if isinstance(view, QueryIndexView):
            msg = 'Cannot delete a query index view using this method.'
            raise CloudantException(msg)

        self.views.__delitem__(view_name)

    def fetch(self):
        """
        Retrieves the remote design document content and populates the locally
        cached DesignDocument dictionary.  View content is stored either as
        View or QueryIndexView objects which are extensions of the ``dict``
        type.  All other design document data are stored directly as
        ``dict`` types.
        """
        super(DesignDocument, self).fetch()
        for view_name, view_def in self.get('views', {}).iteritems():
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

        super(DesignDocument, self).save()

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
        for view_name, view in self.views.iteritems():
            yield view_name, view

    def list_views(self):
        """
        Retrieves a list of available View objects in the locally cached
        DesignDocument.

        :returns: List of view names
        """
        return self.views.keys()

    def get_view(self, view_name):
        """
        Retrieves a specific View from the locally cached DesignDocument by
        name.

        :param str view_name: Name used to identify the View.

        :returns: View object for the specified view_name
        """
        return self.views.get(view_name)

    def info(self):
        """
        Retrieves the design document view information data, returns dictionary

        GET databasename/_design/{ddoc}/_info
        """
        raise NotImplementedError("_info not yet implemented")
