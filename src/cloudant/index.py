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

from ._2to3 import STRTYPE, iteritems_
from ._common_util import (
    JSON_INDEX_TYPE,
    TEXT_INDEX_TYPE,
    SPECIAL_INDEX_TYPE,
    TEXT_INDEX_ARGS,
    SEARCH_INDEX_ARGS,
    codify
)
from .error import CloudantArgumentError, CloudantException

class Index(object):
    """
    Provides an interface for managing a JSON query index.  Primarily
    meant to be used by the database convenience methods
    :func:`~cloudant.database.CloudantDatabase.create_query_index`,
    :func:`~cloudant.database.CloudantDatabase.delete_query_index`, and
    :func:`~cloudant.database.CloudantDatabase.get_query_indexes`.  It is
    recommended that you use those methods to manage an index rather than
    directly interfacing with Index objects.

    :param CloudantDatabase database: A Cloudant database instance used by the
        Index.
    :param str design_document_id: Optional identifier of the design document.
    :param str name: Optional name of the index.
    :param kwargs: Options used to construct the index definition for the
        purposes of index creation.  For more details on valid options See
        :func:`~cloudant.database.CloudantDatabase.create_query_index`.
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
            if isinstance(self._ddoc_id, STRTYPE):
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
            if isinstance(self._name, STRTYPE):
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
        if list(self._def.keys()) != ['fields']:
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

class TextIndex(Index):
    """
    Provides an interface for managing a text query index.  Primarily
    meant to be used by the database convenience methods
    :func:`~cloudant.database.CloudantDatabase.create_query_index`,
    :func:`~cloudant.database.CloudantDatabase.delete_query_index`, and
    :func:`~cloudant.database.CloudantDatabase.get_query_indexes`.  It is
    recommended that you use those methods to manage an index rather than
    directly interfacing with TextIndex objects.

    :param CloudantDatabase database: A Cloudant database instance used by the
        TextIndex.
    :param str design_document_id: Optional identifier of the design document.
    :param str name: Optional name of the index.
    :param kwargs: Options used to construct the index definition for the
        purposes of index creation.  For more details on valid options See
        :func:`~cloudant.database.CloudantDatabase.create_query_index`.
    """
    def __init__(self, database, design_document_id=None, name=None, **kwargs):
        super(TextIndex, self).__init__(
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
        if self._def != dict():
            for key, val in iteritems_(self._def):
                if key not in list(TEXT_INDEX_ARGS.keys()):
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
    :func:`~cloudant.database.CloudantDatabase.get_query_indexes`.  It is
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

class SearchIndex(dict):
    """
    Encapsulates a SearchIndex as a dictionary based object, exposing the
    search index function and analyzer as attributes. A SearchIndex object is
    instantiated with a reference to a DesignDocument and is typically used as
    part of the :class:`~cloudant.design_document.DesignDocument`
    search index management API.

    :param DesignDocument ddoc: DesignDocument instance used in part to
        identify the search index.
    :param str index_name: Name used in part to identify the index.
    :param str search_func: Javascript search index function.
        Optional only if executing a search query.
    :param str analyzer: Optional analyzer of the index.  Defaults to standard.
    """

    def __init__(
            self,
            ddoc,
            index_name,
            search_func=None,
            analyzer='standard'
        ):
        super(SearchIndex, self).__init__()
        self.design_doc = ddoc
        self._r_session = self.design_doc.r_session
        self._encoder = self.design_doc.encoder
        self.index_name = index_name
        if search_func is not None:
            self['index'] = codify(search_func)
        self['analyzer'] = analyzer

    @property
    def analyzer(self):
        """
        Get the analyzer for this index.  Default value is a ``standard``
        analyzer.  For more details on supported analyzers for a Cloudant
        search index, see the analyzer
        `documentation <https://docs.cloudant.com/search.html#analyzers>`_.

        :param str analyzer: Analyzer for this index.

        :returns: Search index analyzer
        """
        return self.get('analyzer')

    @analyzer.setter
    def analyzer(self, analyzer):
        """
        Set the analyzer for this index.
        """
        self['analyzer'] = analyzer

    @property
    def index(self):
        """
        Get the Javascript function for this index.

        For example:

        .. code-block:: python

            # Set the SearchIndex index property
            search.index = 'function (doc) {  index(\"default\", doc._id); }'

        :param str search_func: Javascript search index function.

        :returns: Codified search index function
        """
        return self.get('index')

    @index.setter
    def index(self, search_func):
        """
        Set the Javascript function for this index.
        """
        self['index'] = codify(search_func)

    @property
    def url(self):
        """
        Constructs and returns the Cloudant Search URL.

        :returns: Search URL
        """
        return '/'.join([
            self.design_doc.document_url,
            '_search',
            self.index_name
        ])

    def __call__(self, **kwargs):
        """
        Makes the SearchIndex object callable and retrieves the raw JSON
        content from the remote database based on the search index on the
        server, using the kwargs provided as query parameters.

        Example for search index queries:

        .. code-block:: python

            # Construct a SearchIndex
            search = SearchIndex(ddoc, 'searchindex001')
            # Assuming that 'searchindex001' exists as part of the
            # design document ddoc in the remote database...
            # Use SearchIndex as a callable
            for row in search(query='julia*', include_docs=True)['rows']:
                # Process search index data (in JSON format).

        Example if the search query requires grouping by using
        the ``group_field`` parameter:

        .. code-block:: python

            # Construct a SearchIndex
            search = SearchIndex(ddoc, 'searchindex001')
            # Use SearchIndex as a callable
            response = search(query='julia*', group_field='name')
            for group in response['groups']:
                for row in group['rows']:
                # Process search index data (in JSON format).

        :param str bookmark: A string that enables you to specify which page of
            results you require. Only valid for queries that do not specify the
            ``group_field`` query parameter.
        :param list counts: A JSON array of field names for which counts should
            be produced. The response will contain counts for each unique value
            of this field name among the documents matching the search query.
            Requires the index to have faceting enabled.
        :param list drilldown:  A list of fields that each define a pair of a
            field name and a value. This field can be used several times.
            The search will only match documents that have the given value in
            the field name. It differs from using ``query=fieldname:value``
            only in that the values are not analyzed.
        :param str group_field: A string field by which to group search matches.
            Fields containing other data (numbers, objects, arrays)
            can not be used.
        :param int group_limit: Maximum group count.
            This field can only be used if ``group_field`` query parameter
            is specified.
        :param group_sort: A JSON field that defines the order of the
            groups in a search using ``group_field``. The default sort order
            is relevance. This field can have the same values as the sort field,
            so single fields as well as arrays of fields are supported.
        :param int limit: Limit the number of the returned documents to the
            specified count. In case of a grouped search, this parameter limits
            the number of documents per group.
        :param query: A Lucene query in the form of ``name:value``.
            If name is omitted, the special value ``default`` is used.
        :param ranges: A JSON facet syntax that reuses the standard Lucene
            syntax to return counts of results which fit into each specified
            category. Inclusive range queries are denoted by brackets.
            Exclusive range queries are denoted by curly brackets.
            For example ``ranges={"price":{"cheap":"[0 TO 100]"}}`` has an
            inclusive range of 0 to 100.
            Requires the index to have faceting enabled.
        :param sort: A JSON string of the form ``fieldname<type>`` for ascending
            or ``-fieldname<type>`` for descending sort order. Fieldname is the
            name of a string or number field and type is either number or string
            or a JSON array of such strings. The type part is optional and
            defaults to number.
        :param str stale: Allow the results from a stale index to be used. This
            makes the request return immediately, even if the index has not been
            completely built yet.
        :param list highlight_fields: A list of fields which should be
            highlighted.
        :param str highlight_pre_tag: A string inserted before the highlighted
            word in the highlights output.  Defaults to ``<em>``.
        :param str highlight_post_tag: A string inserted after the highlighted
            word in the highlights output.  Defaults to ``<em>``.
        :param int highlight_number: A number of fragments returned in
            highlights. If the search term occurs less often than the number of
            fragments specified, longer fragments are returned.  Default is 1.
        :param int highlight_size: A number of characters in each fragment for
            highlights.  Defaults to 100 characters.
        :param list include_fields: A list of field names to include in search
            results. Any fields included must have been indexed with the
            ``store:true`` option.

        :returns: Search query result data in JSON format
        """
        # Validate query arguments and values
        for key, val in iteritems_(kwargs):
            if key not in list(SEARCH_INDEX_ARGS.keys()):
                msg = 'Invalid argument: {0}'.format(key)
                raise CloudantArgumentError(msg)
            if not isinstance(val, SEARCH_INDEX_ARGS[key]):
                msg = (
                    'Argument {0} is not an instance of expected type: {1}'
                ).format(key, SEARCH_INDEX_ARGS[key])
                raise CloudantArgumentError(msg)
        if not kwargs.get('query'):
            msg = (
                'Null value or empty lucene search syntax in '
                'the query parameter. Add a search query and retry.'
            )
            raise CloudantArgumentError(msg)
        # Execute query search
        headers = {'Content-Type': 'application/json'}
        resp = self._r_session.post(
            self.url,
            headers=headers,
            data=json.dumps(kwargs, cls=self._encoder)
        )
        resp.raise_for_status()
        return resp.json()
