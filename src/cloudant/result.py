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
API module for interacting with result collections.
"""
import json
import types

from collections import Sequence
from .errors import CloudantArgumentError

ARG_TYPES = {
    'descending': bool,
    'endkey': (basestring, Sequence),
    'endkey_docid': basestring,
    'group': bool,
    'group_level': basestring,
    'include_docs': bool,
    'inclusive_end': bool,
    'key': (int, basestring, Sequence),
    'keys': list,
    'limit': (int, types.NoneType),
    'reduce': bool,
    'skip': (int, types.NoneType),
    'stale': basestring,
    'startkey': (basestring, Sequence),
    'startkey_docid': basestring,
}

# pylint: disable=unnecessary-lambda
TYPE_CONVERTERS = {
    basestring: lambda x: json.dumps(x),
    str: lambda x: json.dumps(x),
    unicode: lambda x: json.dumps(x),
    Sequence: lambda x: json.dumps(list(x)),
    list: lambda x: json.dumps(x),
    tuple: lambda x: json.dumps(list(x)),
    int: lambda x: x,
    bool: lambda x: 'true' if x else 'false',
    types.NoneType: lambda x: x
}

def python_to_couch(options):
    """
    Translates query options from python style options into CouchDB/Cloudant
    query options.  For example ``{'include_docs': True}`` will
    translate to ``{'include_docs': 'true'}``.  Primarily meant for use by
    code that formulates a query to retrieve results data from the
    remote database, such as the database API convenience method
    :func:`~cloudant.database.CouchDatabase.all_docs` or the View
    :func:`~cloudant.views.View.__call__` callable, both used to retrieve data.

    :param dict options: Python style parameters to be translated.

    :returns: Dictionary of translated CouchDB/Cloudant query parameters
    """
    translation = {}
    for key, val in options.iteritems():
        if key not in ARG_TYPES:
            msg = 'Invalid argument {0}'.format(key)
            raise CloudantArgumentError(msg)
        if not isinstance(val, ARG_TYPES[key]):
            msg = 'Argument {0} not instance of expected type: {1}'.format(
                key,
                ARG_TYPES[key]
            )
            raise CloudantArgumentError(msg)
        arg_converter = TYPE_CONVERTERS.get(type(val))
        if key == 'stale':
            if val not in ('ok', 'update_after'):
                msg = (
                    'Invalid value for stale option {0} '
                    'must be ok or update_after'
                ).format(val)
                raise CloudantArgumentError(msg)
        try:
            if val is None:
                translation[key] = None
            else:
                translation[key] = arg_converter(val)
        except Exception as ex:
            msg = 'Error converting argument {0}: {1}'.format(key, ex)
            raise CloudantArgumentError(msg)

    return translation

def type_or_none(typerefs, value):
    """
    Provides a helper function to check that a value is of the types passed or
    None.
    """
    return isinstance(value, typerefs) or value is None

class Result(object):
    """
    Provides a sliceable and iterable interface to result collections.
    A Result object is instantiated with a raw data callable reference
    such as the database API convenience method
    :func:`~cloudant.database.CouchDatabase.all_docs` or the View
    :func:`~cloudant.views.View.__call__` callable, both used to retrieve data.
    A Result object can also use optional extra arguments for result
    customization and supports efficient, paged iteration over the result
    collection to avoid large result data from adversely affecting memory.

    In Python, slicing returns by value, whereas iteration will yield
    elements of the sequence.  This means that slicing will perform better
    for smaller data collections, whereas iteration will be more
    efficient for larger data collections.

    For example:

    .. code-block:: python

        # Access by key:
        result['key'] # get all records matching key

        # Slicing by startkey/endkey:
        result[['2013','10']:['2013','11']] # results between compound keys
        result['2013':'2014']               # results between string keys
        result['2013':]                     # all results after key
        result[:'2014']                     # all results up to key

        # Slicing by value:
        result[100:200] # results between the 100th and the 200th result
        result[:200]    # results up to the 200th result
        result[100:]    # results after 100th result
        result[:]       # all results

        # Iteration:

        # Iterate over the entire result collection
        result = Result(callable)
        for i in result:
            print i

        # Iterate over the result collection between startkey and endkey
        result = Result(callable, startkey='2013', endkey='2014')
        for i in result:
            print i

        # Iterate over the entire result collection,
        # including documents and in batches of a 1000.
        result = Result(callable, include_docs=True, page_size=1000)
        for i in result:
            print i

        :param method_ref: A reference to the method or callable that returns
            the JSON content result to be wrapped.
        :param options: See :func:`~cloudant.views.View.make_result` for a
            list of valid result customization options.
    """
    def __init__(self, method_ref, **options):
        self.options = options
        self._ref = method_ref
        self._page_size = options.pop('page_size', 100)

    def __getitem__(self, key):
        """
        Provides Result key access and slicing support.

        See :class:`~cloudant.result.Result` for key access and slicing
        examples.

        :param key:  Can be either a single value as a ``str`` or ``list``
            which will be passed as the key to the query for entries matching
            that key or slice.  Slices with integers will be interpreted as
            ``skip:limit-skip`` style pairs.  For example ``[100:200]`` means
            skip the first 100 records then get up to and including the 200th
            record so that you get the range between the supplied slice values.
            Slices with strings/lists will be interpreted as startkey/endkey
            style keys.

        :returns: Rows data in JSON format
        """
        if isinstance(key, basestring):
            data = self._ref(key=key, **self.options)
            return self._parse_data(data)

        if isinstance(key, list):
            data = self._ref(key=key, **self.options)
            return self._parse_data(data)

        if isinstance(key, slice):
            # slice is startkey and endkey if str or array
            str_or_none_start = type_or_none((basestring, list), key.start)
            str_or_none_stop = type_or_none((basestring, list), key.stop)
            if str_or_none_start and str_or_none_stop:
                # startkey/endkey
                if key.start is not None and key.stop is not None:
                    data = self._ref(
                        startkey=key.start,
                        endkey=key.stop,
                        **self.options
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(startkey=key.start, **self.options)
                if key.start is None and key.stop is not None:
                    data = self._ref(endkey=key.stop, **self.options)
                if key.start is None and key.stop is None:
                    data = self._ref(**self.options)
                return self._parse_data(data)
            # slice is skip:skip+limit if ints
            int_or_none_start = type_or_none(int, key.start)
            int_or_none_stop = type_or_none(int, key.stop)
            if int_or_none_start and int_or_none_stop:
                if key.start is not None and key.stop is not None:
                    limit = key.stop - key.start
                    data = self._ref(
                        skip=key.start,
                        limit=limit,
                        **self.options
                    )
                if key.start is not None and key.stop is None:
                    data = self._ref(skip=key.start, **self.options)
                if key.start is None and key.stop is not None:
                    data = self._ref(limit=key.stop, **self.options)
                # both None case handled already
                return self._parse_data(data)
        msg = (
            'Failed to interpret the argument {0} '
            'as a valid key value or as a valid slice.'
        ).format(key)
        raise CloudantArgumentError(msg)

    def __iter__(self):
        """
        Provides iteration support, primarily for large data collections.
        The iterator uses the skip/limit parameters to consume data in chunks
        controlled by the ``page_size`` setting and retrieves a batch of data
        from the result collection and then yields each element.  Since the
        iterator uses the skip/limit parameters to perform the iteration,
        ``skip`` and ``limit`` cannot be included as part of the original result
        customization options.

        See :func:`~cloudant.views.View.make_result` for a list of valid
        result customization options.

        See :class:`~cloudant.result.Result` for Result iteration examples.

        :returns: Iterable data sequence
        """
        if 'skip' in self.options:
            msg = 'Cannot use skip for iteration'
            raise CloudantArgumentError(msg)
        if 'limit' in self.options:
            msg = 'Cannot use limit for iteration'
            raise CloudantArgumentError(msg)
        if self._page_size <= 0:
            msg = 'Invalid page_size: {0}'.format(self._page_size)
            raise CloudantArgumentError(msg)

        skip = 0
        while True:
            response = self._ref(
                limit=self._page_size,
                skip=skip,
                **self.options
            )
            result = self._parse_data(response)
            skip = skip + self._page_size
            if len(result) > 0:
                for row in result:
                    yield row
                del result
            else:
                break

    # pylint: disable=no-self-use
    def _parse_data(self, data):
        """
        Used to extract the rows content from the JSON result content
        """
        return data.get('rows', [])

class QueryResult(Result):
    """
    Provides a sliceable and iterable interface to query result collections
    by extending the :class:`~cloudant.result.Result` class.
    A QueryResult object is instantiated with the Query
    :func:`~cloudant.query.Query.__call__` callable, which is used to retrieve
    data.  A QueryResult object can also use optional extra arguments for result
    customization and supports efficient, paged iteration over the result
    collection to avoid large result data from adversely affecting memory.

    In Python, slicing returns by value, whereas iteration will yield
    elements of the sequence.  This means that slicing will perform better
    for smaller data collections, whereas iteration will be more
    efficient for larger data collections.

    For example:

    .. code-block:: python

        # Slicing by value:
        query_result[100:200] # results between the 100th and the 200th result
        query_result[:200]    # results up to the 200th result
        query_result[100:]    # results after 100th result
        query_result[:]       # all results

        # Iteration:

        # Iterate over the entire result collection
        query_result = QueryResult(query)
        for doc in query_result:
            print doc

        # Iterate over the result collection, with an overriding query sort
        query_result = QueryResult(query, sort=[{'name': 'desc'}])
        for doc in query_result:
            print doc

        # Iterate over the entire result collection,
        # explicitly setting the index and in batches of a 1000.
        query_result = QueryResult(query, use_index='my_index', page_size=1000)
        for doc in query_result:
            print doc

        :param query: A reference to the query callable that returns
            the JSON content result to be wrapped.
        :param options: See :func:`~cloudant.query.Query.make_result` for a
            list of valid query result customization options.
    """
    def __init__(self, query, **options):
        super(QueryResult, self).__init__(query, **options)

    def __getitem__(self, key):
        """
        Provides query result slicing by element support.  Key access and
        slicing by non-integer key value are not available for query results.

        See :class:`~cloudant.result.QueryResult` for slicing examples.

        :param key:  Must be a range defined by two integers.  Slices
            will be interpreted as ``skip:limit-skip`` style pairs.
            For example ``[100:200]`` means skip 100 records
            then get up to and including the 200th record so that you get the
            range between the supplied slice values.  Whereas ``[:100]`` means
            get up to and including the 100th record.

        :returns: Rows data in JSON format
        """
        if 'skip' in self.options or 'skip' in self._ref.keys():
            msg = 'Cannot use skip parameter with QueryResult slicing.'
            raise CloudantArgumentError(msg)
        if 'limit' in self.options or 'limit' in self._ref.keys():
            msg = 'Cannot use limit parameter with QueryResult slicing.'
            raise CloudantArgumentError(msg)
        if (
                isinstance(key, slice) and
                type_or_none(int, key.start) and
                type_or_none(int, key.stop)
        ):
            if key.start is None and key.stop is None:
                return [doc for doc in self.__iter__()]
            return super(QueryResult, self).__getitem__(key)
        else:
            msg = (
                'Failed to interpret the argument {0} as an element slice.  '
                'Only slicing by integer values is supported with '
                'QueryResult.__getitem__.'
            ).format(key)
            raise CloudantArgumentError(msg)

    def _parse_data(self, data):
        """
        Overrides Result._parse_data to extract the docs content from the
        query result JSON response content
        """
        return data.get('docs', [])
