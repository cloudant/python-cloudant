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
API module for composing and executing Cloudant queries.
"""

import posixpath
import json
import types
import contextlib

from .result import QueryResult
from .errors import CloudantArgumentError

ARG_TYPES = {
    'selector': dict,
    'limit': (int, types.NoneType),
    'skip': (int, types.NoneType),
    'sort': list,
    'fields': list,
    'r': (int, types.NoneType),
    'bookmark': basestring,
    'use_index': basestring
}

class Query(dict):
    """
    Encapsulates a query as a dictionary based object, providing a sliceable
    and iterable query result collection that can be used to process query
    output data through the ``result`` attribute.

    For example:

    .. code-block:: python

        # Slicing to skip/limit:
        query.result[100:200]
        query.result[:200]
        query.result[100:]
        query.result[:]

        # Iteration is supported via the result attribute:
        for doc in query.result:
            print doc

    The query ``result`` collection provides basic functionality,
    which can be customized with other arguments using the
    :func:`~cloudant.query.Query.custom_result` context.

    For example:

    .. code-block:: python

        # Setting the read quorum as part of a custom result
        with query.custom_result(r=3) as rslt:
            rslt[100:200] # slice the result

            # Iteration
            for doc in rslt:
                print doc

        # Iteration over a query result sorted by the "name" field:
        with query.custom_result(sort=[{'name': 'asc'}]) as rslt:
            for doc in rslt:
                print doc

    :param CloudantDatabase database: A Cloudant database instance used by the
        Query.
    :param str bookmark: A string that enables you to specify which page of
        results you require. Only valid for queries using indexes of type
        *text*.
    :param list fields: A list of fields to be returned by the query.
    :param int limit: Maximum number of results returned.
    :param int r: Read quorum needed for the result.  Each document is read from
        at least 'r' number of replicas before it is returned in the results.
    :param str selector: Dictionary object describing criteria used to select
        documents.
    :param int skip: Skip the first 'n' results, where 'n' is the value
        specified.
    :param list sort: A list of fields to sort by.  Optionally the list can
        contain elements that are single member dictionary structures that
        specify sort direction.  For example ``sort=['name', {'age': 'desc'}]``
        means to sort the query results by the "name" field in ascending order
        and the "age" field in descending order.
    :param str use_index: Identifies a specific index for the query to run
        against, rather than using the Cloudant Query algorithm which finds
        what it believes to be the best index.
    """

    def __init__(self, database, **kwargs):
        super(Query, self).__init__()
        self._database = database
        self._r_session = self._database.r_session
        self._encoder = self._database.cloudant_account.encoder
        if kwargs:
            super(Query, self).update(kwargs)
        self.result = QueryResult(self)

    @property
    def url(self):
        """
        Constructs and returns the Query URL.

        :returns: Query URL
        """
        return posixpath.join(self._database.database_url, '_find')

    def __call__(self, **kwargs):
        """
        Makes the Query object callable and retrieves the raw JSON content
        from the remote database based on the current Query definition,
        and any additional kwargs provided as query parameters.

        For example:

        .. code-block:: python

            # Construct a Query
            query = Query(database, selector={'_id': {'$gt': 0}})
            # Use query as a callable limiting results to 100,
            # skipping the first 100.
            for doc in query(limit=100, skip=100)['docs']:
                # Process query data (in JSON format).

        Note:  Rather than using the Query callable directly, if you wish to
        retrieve query results in raw JSON format use the provided database API
        of :func:`~cloudant.database.CouchDatabase.get_query_result`
        and set ``raw_result=True`` instead.

        :param str bookmark: A string that enables you to specify which page of
            results you require. Only valid for queries using indexes of type
            *text*.
        :param list fields: A list of fields to be returned by the query.
        :param int limit: Maximum number of results returned.
        :param int r: Read quorum needed for the result.  Each document is read
            from at least 'r' number of replicas before it is returned in the
            results.
        :param str selector: Dictionary object describing criteria used to
            select documents.
        :param int skip: Skip the first 'n' results, where 'n' is the value
            specified.
        :param list sort: A list of fields to sort by.  Optionally the list can
            contain elements that are single member dictionary structures that
            specify sort direction.  For example
            ``sort=['name', {'age': 'desc'}]`` means to sort the query results
            by the "name" field in ascending order and the "age" field in
            descending order.
        :param str use_index: Identifies a specific index for the query to run
            against, rather than using the Cloudant Query algorithm which finds
            what it believes to be the best index.

        :returns: Query result data in JSON format
        """
        data = dict(self)
        data.update(kwargs)

        # Validate query arguments and values
        for key, val in data.iteritems():
            if key not in ARG_TYPES.keys():
                msg = 'Invalid argument: {0}'.format(key)
                raise CloudantArgumentError(msg)
            if not isinstance(val, ARG_TYPES[key]):
                msg = (
                    'Argument {0} is not an instance of expected type: {1}'
                ).format(key, ARG_TYPES[key])
                raise CloudantArgumentError(msg)
        if data.get('selector', None) is None or data.get('selector') == {}:
            msg = (
                'No selector in the query or the selector was empty.  '
                'Add a selector to define the query and retry.'
            )
            raise CloudantArgumentError(msg)
        if data.get('fields', None) is None or data.get('fields') == []:
            msg = (
                'No fields list in the query or the fields list was empty.  '
                'Add a list of fields for the query and retry.'
            )
            raise CloudantArgumentError(msg)

        # Execute query find
        headers = {'Content-Type': 'application/json'}
        resp = self._r_session.post(
            self.url,
            headers=headers,
            data=json.dumps(data, cls=self._encoder)
        )
        resp.raise_for_status()
        return resp.json()

    def make_result(self, **options):
        """
        Wraps the raw JSON content of the Query object callable in a
        :class:`~cloudant.result.QueryResult` object.  The use of ``skip``
        and ``limit`` as options are not valid when using a QueryResult since
        the ``skip`` and ``limit`` functionality is handled in the QueryResult.

        Note:  Rather than using this method directly, if you wish to
        retrieve query data as a QueryResult object, use the provided database
        API of :func:`~cloudant.database.CouchDatabase.get_query_result`
        using the ``raw_result=False`` default setting instead.

        :param str bookmark: A string that enables you to specify which page of
            results you require. Only valid for queries using indexes of type
            *text*.
        :param list fields: A list of fields to be returned by the query.
        :param int page_size: Sets the page size for result iteration.  Default
            is 100.
        :param int r: Read quorum needed for the result.  Each document is read
            from at least 'r' number of replicas before it is returned in the
            results.
        :param str selector: Dictionary object describing criteria used to
            select documents.
        :param list sort: A list of fields to sort by.  Optionally the list can
            contain elements that are single member dictionary structures that
            specify sort direction.  For example
            ``sort=['name', {'age': 'desc'}]`` means to sort the query results
            by the "name" field in ascending order and the "age" field in
            descending order.
        :param str use_index: Identifies a specific index for the query to run
            against, rather than using the Cloudant Query algorithm which finds
            what it believes to be the best index.

        :returns: Query result data wrapped in a QueryResult instance
        """
        return QueryResult(self, **options)

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        Customizes the :class:`~cloudant.result.QueryResult` behavior and
        provides a convenient context manager for the QueryResult.  QueryResult
        customizations can be made by providing extra options to the query
        result call using this context manager.  The use of ``skip`` and
        ``limit`` as options are not valid when using a QueryResult since the
        ``skip`` and ``limit`` functionality is handled in the QueryResult.

        For example:

        .. code-block:: python

            with query.custom_result(sort=[{'name': 'asc'}]) as rslt:
                data = rslt[100:200]

        :param str bookmark: A string that enables you to specify which page of
            results you require. Only valid for queries using indexes of type
            *text*.
        :param list fields: A list of fields to be returned by the query.
        :param int page_size: Sets the page size for result iteration.  Default
            is 100.
        :param int r: Read quorum needed for the result.  Each document is read
            from at least 'r' number of replicas before it is returned in the
            results.
        :param str selector: Dictionary object describing criteria used to
            select documents.
        :param list sort: A list of fields to sort by.  Optionally the list can
            contain elements that are single member dictionary structures that
            specify sort direction.  For example
            ``sort=['name', {'age': 'desc'}]`` means to sort the query results
            by the "name" field in ascending order and the "age" field in
            descending order.
        :param str use_index: Identifies a specific index for the query to run
            against, rather than using the Cloudant Query algorithm which finds
            what it believes to be the best index.

        :returns: Query result data wrapped in a QueryResult instance
        """
        rslt = self.make_result(**options)
        yield rslt
        del rslt
