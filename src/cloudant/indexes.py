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
API module for managing/viewing query indexes.
"""

import posixpath
import json

from .index_constants import JSON_INDEX_TYPE
from .index_constants import TEXT_INDEX_TYPE
from .index_constants import SPECIAL_INDEX_TYPE
from .index_constants import TEXT_INDEX_ARGS
from .errors import CloudantArgumentError, CloudantException

class Index(object):
    """
    Provides an interface for managing a query JSON index.  Primarily meant to
    be used by the database convenience methods
    :func:`~cloudant.database.CloudantDatabase.create_index`,
    :func:`~cloudant.database.CloudantDatabase.delete_index`, and
    :func:`~cloudant.database.CloudantDatabase.get_all_indexes`.  It is
    recommended that you use those methods to manage an index rather than
    directly interfacing with Index objects.

    :param CloudantDatabase database: A Cloudant database instance used by the
        Index.
    :param str design_document_id: Optional identifier of the design document.
    :param str name: Optional name of the index.
    :param kwargs: Options used to construct the index definition for the
        purposes of index creation.  For more details on valid options See
        :func:`~cloudant.database.CloudantDatabase.create_index`.
    """

    def __init__(self, database, design_document_id=None, name=None, **kwargs):
        self._database = database
        self._r_session = self._database.r_session
        self._ddoc_id = design_document_id
        self._name = name
        self._type = JSON_INDEX_TYPE
        self._def = kwargs

    @property
    def index_url(self):
        """
        Constructs and returns the index URL.

        :returns: Index URL
        """
        return posixpath.join(self._database.database_url, '_index')

    @property
    def design_document_id(self):
        """
        Displays the design document id.

        :returns: Design document that this index belongs to
        """
        return self._ddoc_id

    @property
    def name(self):
        """
        Displays the index name.

        :returns: Name for this index
        """
        return self._name

    @property
    def type(self):
        """
        Displays the index type.

        :returns: Type of this index
        """
        return self._type

    @property
    def definition(self):
        """
        Displays the index definition.  This could be either the definiton to
        be used to construct the index or the definition as it is returned by
        a GET request to the *_index* endpoint.

        :returns: Index definition as a dictionary
        """
        return self._def

    def as_a_dict(self):
        """
        Displays the index as a dictionary.  This includes the design document
        id, index name, index type, and index definition.

        :returns: Dictionary representation of the index as a dictionary
        """
        index_dict = {
            'ddoc': self._ddoc_id,
            'name': self._name,
            'type': self._type,
            'def': self._def
        }

        return index_dict

    def create(self):
        """
        Creates the current index in the remote database.
        """
        payload = {'type': self._type}
        if self._ddoc_id and self._ddoc_id != '':
            if isinstance(self._ddoc_id, basestring):
                if self._ddoc_id.startswith('_design/'):
                    payload['ddoc'] = self._ddoc_id[8:]
                else:
                    payload['ddoc'] = self._ddoc_id
            else:
                msg = (
                    'The design document id: {0} is not a string.'
                ).format(self._ddoc_id)
                raise CloudantArgumentError(msg)
        if self._name and self._name != '':
            if isinstance(self._name, basestring):
                payload['name'] = self._name
            else:
                msg = 'The index name: {0} is not a string.'.format(self._name)
                raise CloudantArgumentError(msg)
        self._def_check()
        payload['index'] = self._def

        headers = {'Content-Type': 'application/json'}
        resp = self._r_session.post(
            self.index_url,
            data=json.dumps(payload),
            headers=headers
        )
        resp.raise_for_status()
        self._ddoc_id = resp.json()['id']
        self._name = resp.json()['name']
        return

    def _def_check(self):
        """
        Checks that the only definition provided is a "fields" definition.
        """
        if self._def.keys() != ['fields']:
            msg = (
                '{0} provided as argument(s).  A JSON index requires that '
                'only a \'fields\' argument is provided.'
            ).format(self._def)
            raise CloudantArgumentError(msg)

    def delete(self):
        """
        Removes the current index from the remote database.
        """
        if not self._ddoc_id:
            msg = 'Deleting an index requires a design document id be provided.'
            raise CloudantArgumentError(msg)
        if not self._name:
            msg = 'Deleting an index requires an index name be provided.'
            raise CloudantArgumentError(msg)
        ddoc_id = self._ddoc_id
        if ddoc_id.startswith('_design/'):
            ddoc_id = ddoc_id[8:]
        url = posixpath.join(self.index_url, ddoc_id, self._type, self._name)
        resp = self._r_session.delete(url)
        resp.raise_for_status()
        return

class SearchIndex(Index):
    """
    Provides an interface for managing a query text index.  Primarily meant to
    be used by the database convenience methods
    :func:`~cloudant.database.CloudantDatabase.create_index`,
    :func:`~cloudant.database.CloudantDatabase.delete_index`, and
    :func:`~cloudant.database.CloudantDatabase.get_all_indexes`.  It is
    recommended that you use those methods to manage an index rather than
    directly interfacing with SearchIndex objects.

    :param CloudantDatabase database: A Cloudant database instance used by the
        SearchIndex.
    :param str design_document_id: Optional identifier of the design document.
    :param str name: Optional name of the index.
    :param kwargs: Options used to construct the index definition for the
        purposes of index creation.  For more details on valid options See
        :func:`~cloudant.database.CloudantDatabase.create_index`.
    """
    def __init__(self, database, design_document_id=None, name=None, **kwargs):
        super(SearchIndex, self).__init__(
            database,
            design_document_id,
            name,
            **kwargs
        )
        self._type = TEXT_INDEX_TYPE

    def _def_check(self):
        """
        Checks that the definition provided contains only valid arguments for a
        text index.
        """
        if self._def != {}:
            for key, val in self._def.iteritems():
                if key not in TEXT_INDEX_ARGS.keys():
                    msg = 'Invalid argument: {0}'.format(key)
                    raise CloudantArgumentError(msg)
                if not isinstance(val, TEXT_INDEX_ARGS[key]):
                    msg = (
                        'Argument {0} is not an instance of expected type: {1}'
                    ).format(key, TEXT_INDEX_ARGS[key])
                    raise CloudantArgumentError(msg)

class SpecialIndex(Index):
    """
    Provides an interface for viewing the "special" primary index of a database.
    Primarily meant to be used by the database convenience method
    :func:`~cloudant.database.CloudantDatabase.get_all_indexes`.  It is
    recommended that you use that method to view the "special" index rather than
    directly interfacing with the SpecialIndex object.
    """
    def __init__(
            self,
            database,
            design_document_id=None,
            name='_all_docs',
            **kwargs
    ):
        super(SpecialIndex, self).__init__(
            database,
            design_document_id,
            name,
            **kwargs
        )
        self._type = SPECIAL_INDEX_TYPE

    def create(self):
        """
        A "special" index cannot be created.  This method is disabled for a
        SpecialIndex object.
        """
        msg = 'Creating the \"special\" index is not allowed.'
        raise CloudantException(msg)

    def delete(self):
        """
        A "special" index cannot be deleted.  This method is disabled for a
        SpecialIndex object.
        """
        msg = 'Deleting the \"special\" index is not allowed.'
        raise CloudantException(msg)
