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
from collections import Sequence

from ._2to3 import STRTYPE, UNITYPE, NONETYPE, iteritems_
from .errors import CloudantArgumentError, ResultException

ARG_TYPES = {
    'descending': (bool,),
    'endkey': (int, STRTYPE, Sequence,),
    'endkey_docid': (STRTYPE,),
    'group': (bool,),
    'group_level': (int, NONETYPE,),
    'include_docs': (bool,),
    'inclusive_end': (bool,),
    'key': (int, STRTYPE, Sequence,),
    'keys': (list,),
    'limit': (int, NONETYPE,),
    'reduce': (bool,),
    'skip': (int, NONETYPE,),
    'stale': (STRTYPE,),
    'startkey': (int, STRTYPE, Sequence,),
    'startkey_docid': (STRTYPE,),
}

# pylint: disable=unnecessary-lambda
TYPE_CONVERTERS = {
    STRTYPE: lambda x: json.dumps(x),
    str: lambda x: json.dumps(x),
    UNITYPE: lambda x: json.dumps(x),
    Sequence: lambda x: json.dumps(list(x)),
    list: lambda x: json.dumps(x),
    tuple: lambda x: json.dumps(list(x)),
    int: lambda x: x,
    bool: lambda x: 'true' if x else 'false',
    NONETYPE: lambda x: x
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
    translation = dict()
    for key, val in iteritems_(options):
        _validate(key, val)
        translation.update(_translate(key, val))
    return translation

def _validate(key, val):
    """
    Validates the individual parameter key and value.
    """
    if key not in ARG_TYPES:
        msg = 'Invalid argument {0}'.format(key)
        raise CloudantArgumentError(msg)
    # pylint: disable=unidiomatic-typecheck
    # Validate argument values and ensure that a boolean is not passed in
    # if an integer is expected
    if (not isinstance(val, ARG_TYPES[key]) or
            (type(val) is bool and int in ARG_TYPES[key])):
        msg = 'Argument {0} not instance of expected type: {1}'.format(
            key,
            ARG_TYPES[key]
        )
        raise CloudantArgumentError(msg)
    if key == 'keys':
        for key_list_val in val:
            if (not isinstance(key_list_val, ARG_TYPES['key']) or
                    type(key_list_val) is bool):
                msg = 'Key list element not of expected type: {0}'.format(
                    ARG_TYPES['key']
                )
                raise CloudantArgumentError(msg)
    if key == 'stale':
        if val not in ('ok', 'update_after'):
            msg = (
                'Invalid value for stale option {0} '
                'must be ok or update_after'
            ).format(val)
            raise CloudantArgumentError(msg)

def _translate(key, val):
    """
    Performs the conversion of the Python parameter value to its CouchDB
    equivalent.
    """
    try:
        if key in ['keys', 'endkey_docid', 'startkey_docid', 'stale']:
            return {key: val}
        elif val is None:
            return {key: None}
        else:
            arg_converter = TYPE_CONVERTERS.get(type(val))
            return {key: arg_converter(val)}
    except Exception as ex:
        msg = 'Error converting argument {0}: {1}'.format(key, ex)
        raise CloudantArgumentError(msg)

def type_or_none(typerefs, value):
    """
    Provides a helper function to check that a value is of the types passed or
    None.
    """
    return isinstance(value, typerefs) or value is None

class ResultByKey(object):
    """
    Provides a wrapper for a value used to retrieve records from a result
    collection based on an actual document key value.  This comes in handy when
    the document key value is an ``int``.

    For example:

    .. code-block:: python

        result = Result(callable)
        result[ResultByKey(9)]   # gets records where the key matches 9
        # as opposed to:
        result[9]                # gets the 10th record of the result collection

        :param value: A value representing a Result key.
    """
    def __init__(self, value):
        self._value = value

    def __call__(self):
        return self._value

class Result(object):
    """
    Provides a key accessible, sliceable, and iterable interface to result
    collections.  A Result object is constructed with a raw data callable
    reference such as the database API convenience method
    :func:`~cloudant.database.CouchDatabase.all_docs` or the View
    :func:`~cloudant.views.View.__call__` callable, used to retrieve data.
    A Result object can also use optional extra arguments for result
    customization and supports efficient, paged iteration over the result
    collection to avoid large result data from adversely affecting memory.

    In Python, slicing returns by value, whereas iteration will yield
    elements of the sequence.  This means that individual key access and slicing
    will perform better for smaller data collections, whereas iteration will
    be more efficient for larger data collections.

    For example:

    .. code-block:: python

        # Key access:

        # Access by index value:
        result = Result(callable)
        result(9)                 # skip first 9 records and get 10th

        # Access by key value:
        result = Result(callable)
        result['foo']             # get records matching 'foo'
        result[ResultByKey(9)]    # get records matching 9

        # Slice access:

        # Access by index slices:
        result = Result(callable)
        result[100: 200]          # get records after the 100th and up to and including the 200th
        result[: 200]             # get records up to and including the 200th
        result[100: ]             # get all records after the 100th
        result[: ]                # get all records

        # Access by key slices:
        result = Result(callable)
        result['bar':'foo']       # get records between and including 'bar' and 'foo'
        result['foo':]            # get records after and including 'foo'
        result[:'foo']            # get records up to and including 'foo'

        result[['foo', 10]:
               ['foo', 11]]       # Complex key access and slicing works the same as simple keys

        result[ResultByKey(5):
               ResultByKey(10)]   # key slice access of integer keys

        # Iteration:

        # Iterate over the entire result collection
        result = Result(callable)
        for i in result:
            print i

        # Iterate over the result collection between startkey and endkey
        result = Result(callable, startkey='2013', endkey='2014')
        for i in result:
            print i

        # Iterate over the entire result collection in batches of 1000, including documents.
        result = Result(callable, include_docs=True, page_size=1000)
        for i in result:
            print i

    Note: Since Result object key access, slicing, and iteration use query
    parameters behind the scenes to handle their processing, some query
    parameters are not permitted as part of a Result customization,
    depending on whether key access, slicing, or iteration is being performed.

    Such as:

    +-------------------------------+-----------------------------------------------------------+
    | Access/Slicing by index value | No restrictions                                           |
    +-------------------------------+-----------------------------------------------------------+
    | Access/Slicing by key value   | ``key``, ``keys``, ``startkey``, ``endkey`` not permitted |
    +-------------------------------+-----------------------------------------------------------+
    | Iteration                     | ``limit``, ``skip`` not permitted                         |
    +-------------------------------+-----------------------------------------------------------+

    :param method_ref: A reference to the method or callable that returns
        the JSON content result to be wrapped as a Result.
    :param options: See :func:`~cloudant.views.View.make_result` for a
        list of valid result customization options.
    """
    def __init__(self, method_ref, **options):
        self.options = options
        self._ref = method_ref
        self._page_size = options.pop('page_size', 100)

    def __getitem__(self, arg):
        """
        Provides Result key access and slicing support.

        An ``int`` argument will be interpreted as a ``skip`` and then a get of
        the next record.  For example ``[100]`` means skip the first 100 records
        and then get the next record.

        A ``str``, ``list`` or :class:`~cloudant.result.ResultByKey` argument
        will be interpreted as a ``key`` and then get all records that match the
        given key.  For example ``['foo']`` will get all records that match
        the key 'foo'.

        An ``int`` slice argument will be interpreted as a ``skip:limit-skip``
        style pair.  For example ``[100: 200]`` means skip the first 100 records
        then get up to and including the 200th record so that you get the range
        between the supplied slice values.

        A slice argument that contains ``str``, ``list``, or
        :class:`~cloudant.result.ResultByKey` will be interpreted as a
        ``startkey: endkey`` style pair.  For example ``['bar': 'foo']`` means
        get the range of records where the keys are between and including
        'bar' and 'foo'.

        See :class:`~cloudant.result.Result` for more detailed key access and
        slicing examples.

        :param arg:  A single value representing a key or a pair of values
            representing a slice.  The argument value(s) can be ``int``,
            ``str``, ``list`` (in the case of complex keys), or
            :class:`~cloudant.result.ResultByKey`.

        :returns: Rows data as a list in JSON format
        """
        data = None
        if isinstance(arg, int):
            data = self._handle_result_by_index(arg)
        elif isinstance(arg, STRTYPE) or isinstance(arg, list):
            data = self._handle_result_by_key(arg)
        elif isinstance(arg, ResultByKey):
            data = self._handle_result_by_key(arg())
        elif isinstance(arg, slice):
            # slice is entire result set - no additional processing required
            if arg.start is None and arg.stop is None:
                data = self._ref(**self.options)
            # key slice identified
            elif (type_or_none((STRTYPE, list, ResultByKey), arg.start) and
                  type_or_none((STRTYPE, list, ResultByKey), arg.stop)):
                data = self._handle_result_by_key_slice(arg)
            # index slice identified
            elif (type_or_none(int, arg.start) and
                  type_or_none(int, arg.stop)):
                data = self._handle_result_by_idx_slice(arg)
        if data is None:
            raise ResultException(101, arg)
        return self._parse_data(data)

    def _handle_result_by_index(self, idx):
        """
        Handle processing when the result argument provided is an integer.
        """
        if idx < 0:
            return None
        opts = dict(self.options)
        skip = opts.pop('skip', 0)
        limit = opts.pop('limit', None)
        _validate('skip', skip)
        _validate('limit', limit)
        if limit is not None and idx >= limit:
            # Result is out of range
            return dict()
        return self._ref(skip=skip+idx, limit=1, **opts)

    def _handle_result_by_key(self, key):
        """
        Handle processing when the result argument provided is a document key.
        """
        invalid_options = ('key', 'keys', 'startkey', 'endkey')
        if any(x in invalid_options for x in self.options):
            raise ResultException(102, invalid_options, self.options)
        return self._ref(key=key, **self.options)

    def _handle_result_by_idx_slice(self, idx_slice):
        """
        Handle processing when the result argument provided is an index slice.
        """
        opts = dict(self.options)
        skip = opts.pop('skip', 0)
        limit = opts.pop('limit', None)
        _validate('skip', skip)
        _validate('limit', limit)
        start = idx_slice.start
        stop = idx_slice.stop
        data = None
        if (start is not None and stop is not None and
                start >= 0 and stop >= 0 and start <= stop):
            if limit is not None:
                if start >= limit:
                    # Result is out of range
                    return dict()
                elif stop > limit:
                    # Ensure that slice does not extend past original limit
                    return self._ref(skip=skip+start, limit=limit-start, **opts)
            data = self._ref(skip=skip+start, limit=stop-start, **opts)
        elif start is not None and stop is None and start >= 0:
            if limit is not None:
                if start >= limit:
                    # Result is out of range
                    return dict()
                # Ensure that slice does not extend past original limit
                data = self._ref(skip=skip+start, limit=limit-start, **opts)
            else:
                data = self._ref(skip=skip+start, **opts)
        elif start is None and stop is not None and stop >= 0:
            if limit is not None and stop > limit:
                # Ensure that slice does not extend past original limit
                data = self._ref(skip=skip, limit=limit, **opts)
            else:
                data = self._ref(skip=skip, limit=stop, **opts)
        return data

    def _handle_result_by_key_slice(self, key_slice):
        """
        Handle processing when the result argument provided is a key slice.
        """
        invalid_options = ('key', 'keys', 'startkey', 'endkey')
        if any(x in invalid_options for x in self.options):
            raise ResultException(102, invalid_options, self.options)

        if isinstance(key_slice.start, ResultByKey):
            start = key_slice.start()
        else:
            start = key_slice.start

        if isinstance(key_slice.stop, ResultByKey):
            stop = key_slice.stop()
        else:
            stop = key_slice.stop

        if (start is not None and stop is not None and
                isinstance(start, type(stop))):
            data = self._ref(startkey=start, endkey=stop, **self.options)
        elif start is not None and stop is None:
            data = self._ref(startkey=start, **self.options)
        elif start is None and stop is not None:
            data = self._ref(endkey=stop, **self.options)
        else:
            data = None
        return data

    def __iter__(self):
        """
        Provides iteration support, primarily for large data collections.
        The iterator uses the ``skip`` and ``limit`` options to consume
        data in chunks controlled by the ``page_size`` option.  It retrieves
        a batch of data from the result collection and then yields each
        element.

        See :func:`~cloudant.views.View.make_result` for a list of valid
        result customization options.

        See :class:`~cloudant.result.Result` for Result iteration examples.

        :returns: Iterable data sequence
        """
        invalid_options = ('skip', 'limit')
        if any(x in invalid_options for x in self.options):
            raise ResultException(103, invalid_options, self.options)

        try:
            if int(self._page_size) <= 0:
                raise ResultException(104, self._page_size)
        except ValueError:
            raise ResultException(104, self._page_size)

        skip = 0
        while True:
            response = self._ref(
                limit=int(self._page_size),
                skip=skip,
                **self.options
            )
            result = self._parse_data(response)
            skip += int(self._page_size)
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
        refkeys = set(self._ref.keys())
        if 'skip' in self.options or 'skip' in refkeys:
            msg = 'Cannot use skip parameter with QueryResult slicing.'
            raise CloudantArgumentError(msg)
        if 'limit' in self.options or 'limit' in refkeys:
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
