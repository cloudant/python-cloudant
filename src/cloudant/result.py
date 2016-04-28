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
from ._2to3 import STRTYPE
from .error import ResultException
from ._common_util import py_to_couch_validate, type_or_none

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
    :func:`~cloudant.view.View.__call__` callable, used to retrieve data.
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
        result[9]                 # skip first 9 records and get 10th

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

    :param str method_ref: A reference to the method or callable that returns
        the JSON content result to be wrapped as a Result.
    :param bool descending: Return documents in descending key order.
    :param endkey: Stop returning records at this specified key.
        Not valid when used with key access and key slicing.
    :param str endkey_docid: Stop returning records when the specified
        document id is reached.
    :param bool group: Using the reduce function, group the results to a
        group or single row.
    :param group_level: Only applicable if the view uses complex keys: keys
        that are JSON arrays. Groups reduce results for the specified number
        of array fields.
    :param bool include_docs: Include the full content of the documents.
    :param bool inclusive_end: Include rows with the specified endkey.
    :param key: Return only documents that match the specified key.
        Not valid when used with key access and key slicing.
    :param list keys: Return only documents that match the specified keys.
        Not valid when used with key access and key slicing.
    :param int limit: Limit the number of returned documents to the
        specified count.  Not valid when used with key iteration.
    :param int page_size: Sets the page size for result iteration.
    :param bool reduce: True to use the reduce function, false otherwise.
    :param int skip: Skip this number of rows from the start.
        Not valid when used with key iteration.
    :param str stale: Allow the results from a stale view to be used. This
        makes the request return immediately, even if the view has not been
        completely built yet. If this parameter is not given, a response is
        returned only after the view has been built.
    :param startkey: Return records starting with the specified key.
        Not valid when used with key access and key slicing.
    :param str startkey_docid: Return records starting with the specified
        document ID.
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
        py_to_couch_validate('skip', skip)
        py_to_couch_validate('limit', limit)
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
        py_to_couch_validate('skip', skip)
        py_to_couch_validate('limit', limit)
        start = idx_slice.start
        stop = idx_slice.stop
        data = None
        if (start is not None and stop is not None and
                start >= 0 and stop >= 0 and start < stop):
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
    Provides a index key accessible, sliceable and iterable interface to query
    result collections by extending the :class:`~cloudant.result.Result` class.
    A QueryResult object is constructed with a raw data callable reference to
    the Query :func:`~cloudant.query.Query.__call__` callable, which is used to
    retrieve data.  A QueryResult object can also use optional extra arguments
    for result customization and supports efficient, paged iteration over the
    result collection to avoid large result data from adversely affecting
    memory.

    In Python, slicing returns by value, whereas iteration will yield
    elements of the sequence.  This means that index key access and slicing will
    perform better for smaller data collections, whereas iteration will be more
    efficient for larger data collections.

    For example:

    .. code-block:: python

        # Key access:

        # Access by index value:
        query_result = QueryResult(query)
        query_result[9]        # skip first 9 documents and get 10th

        # Slice access:

        # Access by index slices:
        query_result = QueryResult(query)
        query_result[100: 200] # get documents after the 100th and up to and including the 200th
        query_result[ :200]    # get documents up to and including the 200th
        query_result[100: ]    # get all documents after the 100th
        query_result[: ]       # get all documents

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
        # explicitly setting the index and in batches of 1000.
        query_result = QueryResult(query, use_index='my_index', page_size=1000)
        for doc in query_result:
            print doc

    Note: Only access by index value, slicing by index values and iteration are
    supported by QueryResult.  Also, since QueryResult object iteration uses the
    ``skip`` and ``limit`` query parameters to handle its processing, ``skip``
    and ``limit`` are not permitted to be part of the query callable or be
    included as part of the QueryResult customized parameters.

    :param query: A reference to the query callable that returns
        the JSON content result to be wrapped.
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
    """
    def __init__(self, query, **options):
        # Move skip/limit to options so super class Result can handle as needed.
        if 'skip' in query and 'skip' not in options:
            options['skip'] = query['skip']
        if 'limit' in query and 'limit' not in options:
            options['limit'] = query['limit']
        super(QueryResult, self).__init__(query, **options)

    def __getitem__(self, arg):
        """
        Provides QueryResult index access and index slicing support.

        An ``int`` argument will be interpreted as a ``skip`` and then a get of
        the next document.  For example ``[100]`` means skip the first 100
        documents and then get the next document.

        An ``int`` slice argument will be interpreted as a ``skip:limit-skip``
        style pair.  For example ``[100: 200]`` means skip the first 100
        documents then get up to and including the 200th document so that you
        get the range between the supplied slice values.

        See :class:`~cloudant.result.QueryResult` for more detailed index access
        and index slicing examples.

        :param arg:  A single value representing a key or a pair of values
            representing a slice.  The argument value(s) must be ``int``.

        :returns: Document data as a list in JSON format
        """
        # Argument can only be an integer or an integer slice.
        if ((isinstance(arg, int)) or
                (isinstance(arg, slice) and
                 type_or_none(int, arg.start) and
                 type_or_none(int, arg.stop))):
            return super(QueryResult, self).__getitem__(arg)
        else:
            raise ResultException(101, arg)

    def _parse_data(self, data):
        """
        Overrides Result._parse_data to extract the docs content from the
        query result JSON response content
        """
        return data.get('docs', [])
