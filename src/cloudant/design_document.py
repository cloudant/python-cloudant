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
from .views import View
from .errors import CloudantArgumentError

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
        either a ``CouchDatabase`` or ``CloudantDatabase` instance.
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

    def add_view(self, view_name, map_func, reduce_func=None):
        """
        Appends a View to the locally cached DesignDocument View dictionary,
        given a map function and optional reduce function.

        :param str view_name: Name used to identify the View.
        :param str map_func: Javascript map function.  Can also be a
            :class:`~cloudant.views.Code` object.
        :param str reduce_func: Optional Javascript reduce function.
            Can also be a :class:`~cloudant.views.Code` object.
        """
        if self.get_view(view_name) is not None:
            msg = "View {0} already exists in this design doc".format(view_name)
            raise CloudantArgumentError(msg)
        view = View(self, view_name, map_func, reduce_func)
        self.views.__setitem__(view_name, view)

    def update_view(self, view_name, map_func, reduce_func=None):
        """
        Modifies an existing View in the locally cached DesignDocument View
        dictionary, given a map function and optional reduce function.

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
        view.map = map_func
        if reduce_func is not None:
            view.reduce = reduce_func
        self.views.__setitem__(view_name, view)

    def delete_view(self, view_name):
        """
        Removes a View from the locally cached DesignDocument View dictionary.

        :param str view_name: Name used to identify the View.
        """
        if self.get_view(view_name) is not None:
            self.views.__delitem__(view_name)

    def fetch(self):
        """
        Retrieves the remote Document content and populates the locally cached
        DesignDocument View dictionary.

        Note:  Other structures to follow...
        """
        super(DesignDocument, self).fetch()
        for view_name, view_def in self.get('views', {}).iteritems():
            self['views'][view_name] = View(
                self,
                view_name,
                view_def.get('map'),
                view_def.get('reduce')
            )

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
