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
API module for interacting with a view in a design document.
"""
import contextlib
import posixpath

from .result import Result, python_to_couch
from .errors import CloudantArgumentError, CloudantException

class Code(str):
    """
    Wraps a ``str`` object as a Code object providing the means to handle
    Javascript blob content.  Used internally by the View object when
    codifying map and reduce Javascript content.
    """
    def __init__(self, code):
        super(Code, self).__init__(code)

def _codify(code_or_str):
    """
    Provides a helper to rationalize code content.
    """
    if code_or_str is None:
        return None
    if not isinstance(code_or_str, Code):
        return Code(code_or_str)
    return code_or_str

class View(dict):
    """
    Encapsulates a view as a dictionary based object, exposing the map and
    reduce functions as attributes and supporting query/data access through
    the view.  A View object is instantiated with a reference to a
    DesignDocument and is typically used as part of the
    :class:`~cloudant.design_document.DesignDocument` view management API.

    A View object provides a sliceable and iterable default result collection
    that can be used to query the view data through the ``result`` attribute.

    For example:

    .. code-block:: python

        # Using integers to skip/limit:
        view.result[100:200]
        view.result[:200]
        view.result[100:]

        # Using strings or lists as startkey/endkey:
        view.result[['2013','10']:['2013','11']]
        view.result[['2013','10']]
        view.result[['2013','10']:]

        # Iteration is supported via the result attribute:
        for doc in view.result:
            print doc

    The default ``result`` collection provides basic functionality,
    which can be customized with other arguments using the
    :func:`~cloudant.views.View.custom_result` context.

    For example:

    .. code-block:: python

        # Including documents as part of a custom result
        with view.custom_result(include_docs=True) as rslt:
            rslt[100:200] # slice by result
            rslt[['2013','10']:['2013','11']] # slice by startkey/endkey

            # Iteration
            for doc in rslt:
                print doc

        # Iteration over a view within startkey/endkey range:
        with view.custom_result(startkey='2013', endkey='2014') as rslt:
            for doc in rslt:
                print doc

    Note:  A view must exist as part of a design document remotely in order to
    access result content as depicted in the above examples.

    :param DesignDocument ddoc: DesignDocument instance used in part to
        identify the view.
    :param str view_name: Name used in part to identify the view.
    :param str map_func: Optional Javascript map function.  Can also be a
        :class:`~cloudant.views.Code` object.
    :param str reduce_func: Optional Javascript reduce function.  Can also be a
        :class:`~cloudant.views.Code` object.
    """
    def __init__(
            self,
            ddoc,
            view_name,
            map_func=None,
            reduce_func=None,
            **kwargs
    ):
        super(View, self).__init__()
        self.design_doc = ddoc
        self._r_session = self.design_doc.r_session
        self.view_name = view_name
        if map_func is not None:
            self['map'] = _codify(map_func)
        if reduce_func is not None:
            self['reduce'] = _codify(reduce_func)
        self.update(kwargs)
        self.result = Result(self)

    @property
    def map(self):
        """
        Provides an map property accessor and setter.  A ``str`` or a ``Code``
        object is acceptable when setting the map property.

        For example:

        .. code-block:: python

            # Set the View map property
            view.map = 'function (doc) {\\n  emit(doc._id, 1);\\n}'
            print view.map

        :param str js_func: Javascript function.  Can also be a
            :class:`~cloudant.views.Code` object.

        :returns: Codified map function
        """
        return self.get('map')

    @map.setter
    def map(self, js_func):
        """
        Provides a map property setter, accepts ``str`` or ``Code`` object.
        """
        self['map'] = _codify(js_func)

    @property
    def reduce(self):
        """
        Provides an reduce property accessor and setter.  A ``str`` or a
        ``Code`` object is acceptable when setting the reduce property.

        For example:

        .. code-block:: python

            # Set the View reduce property
            view.reduce = '_count'
            # Get and print the View reduce property
            print view.reduce

        :param str js_func: Javascript function.  Can also be a
            :class:`~cloudant.views.Code` object.

        :returns: Codified reduce function
        """
        return self.get('reduce')

    @reduce.setter
    def reduce(self, js_func):
        """
        Provides a reduce property setter, accepts ``str`` or ``Code`` object.
        """
        self['reduce'] = _codify(js_func)

    @property
    def url(self):
        """
        Constructs and returns the View URL.

        :returns: View URL
        """
        return posixpath.join(
            self.design_doc.document_url,
            '_view',
            self.view_name
        )

    def __call__(self, **kwargs):
        """
        Makes the View object callable and retrieves the raw JSON content
        from the remote database based on the View definition on the server,
        using the kwargs provided as query parameters.

        For example:

        .. code-block:: python

            # Construct a View
            view = View(ddoc, 'view001')
            # Assuming that 'view001' exists as part of the
            # design document ddoc in the remote database...
            # Use view as a callable
            for row in view(include_docs=True, limit=100, skip=100)['rows']:
                # Process view data (in JSON format).

        Note:  Rather than using the View callable directly, if you wish to
        retrieve view results in raw JSON format use the provided database API
        of :func:`~cloudant.database.CouchDatabase.get_view_raw_result` instead.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are JSON arrays. Groups reduce results for the specified number
            of array fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int limit: Limit the number of returned documents to the
            specified count.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param int skip: Skip this number of rows from the start.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or ``list``
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: View result data in JSON format
        """
        params = python_to_couch(kwargs)
        resp = self._r_session.get(self.url, params=params)
        resp.raise_for_status()
        return resp.json()

    def make_result(self, **options):
        """
        Wraps the raw JSON content of the View object callable in a
        :class:`~cloudant.result.Result` object.  The use of ``skip``
        and ``limit`` as options are not valid when using a Result since the
        ``skip`` and ``limit`` functionality is handled in the Result.

        Note:  Rather than using this method directly, if you wish to
        retrieve view data as a Result object, use the provided database
        API of :func:`~cloudant.database.CouchDatabase.get_view_result` instead.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are JSON arrays. Groups reduce results for the specified number
            of array fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int page_size: Sets the page size for result iteration.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or ``list``
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: View result data wrapped in a Result instance
        """
        return Result(self, **options)

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        Customizes the :class:`~cloudant.result.Result` behavior and provides
        a convenient context manager for the Result.  Result customizations
        can be made by providing extra options to the result call using this
        context manager.  The use of ``skip`` and ``limit`` as options are not
        valid when using a Result since the ``skip`` and ``limit``
        functionality is handled in the Result.

        For example:

        .. code-block:: python

            with view.custom_result(include_docs=True, reduce=False) as rslt:
                data = rslt[100:200]

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are JSON arrays. Groups reduce results for the specified number
            of array fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int page_size: Sets the page size for result iteration.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or ``list``
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: View result data wrapped in a Result instance
        """
        rslt = self.make_result(**options)
        yield rslt
        del rslt

class QueryIndexView(View):
    """
    A view that defines a JSON index in a design document.

    If you wish to manage a view that represents a query index it is strongly
    recommended that :func:`~cloudant.database.CloudantDatabase.create_index`
    and :func:`~cloudant.database.CloudantDatabase.delete_index` are used.
    """
    def __init__(self, ddoc, view_name, map_fields, reduce_func, **kwargs):
        if not isinstance(map_fields, dict):
            raise CloudantArgumentError('The map property must be a dictionary')
        if not isinstance(reduce_func, basestring):
            raise CloudantArgumentError('The reduce property must be a string.')
        super(QueryIndexView, self).__init__(
            ddoc,
            view_name,
            map_fields,
            reduce_func,
            **kwargs
        )
        self['map'] = map_fields
        self['reduce'] = reduce_func
        self.result = None

    @property
    def map(self):
        """
        Provides a map property accessor and setter.

        :param dict map_func: A dictionary of fields defining the index.

        :returns: Fields defining the index
        """
        return self.get('map')

    @map.setter
    def map(self, map_func):
        """
        Provides a map property setter.
        """
        if isinstance(map_func, dict):
            self['map'] = map_func
        else:
            raise CloudantArgumentError('The map property must be a dictionary')

    @property
    def reduce(self):
        """
        Provides a reduce property accessor and setter.

        :param str reduce_func: A string representation of the reduce function
            used in part to define the index.

        :returns: Reduce function as a string
        """
        return self.get('reduce')

    @reduce.setter
    def reduce(self, reduce_func):
        """
        Provides a reduce property setter.
        """
        if isinstance(reduce_func, basestring):
            self['reduce'] = reduce_func
        else:
            raise CloudantArgumentError('The reduce property must be a string')

    def __call__(self, **kwargs):
        """
        QueryIndexView objects are not callable.  If you wish to execute a query
        using a query index, use
        :func:`~cloudant.database.CloudantDatabase.get_query_result` instead.
        """
        raise CloudantException(
            'A QueryIndexView is not callable.  If you wish to execute a query '
            'use the database \'get_query_result\' convenience method.'
        )

    def make_result(self, **options):
        """
        This method overrides the View base class
        :func:`~cloudant.views.View.make_result` method with the sole purpose of
        disabling it.  Since QueryIndexView objects are not callable, there is
        no reason to wrap their output in a Result.  If you wish to execute a
        query using a query index, use
        :func:`~cloudant.database.CloudantDatabase.get_query_result` instead.
        """
        raise CloudantException(
            'Cannot make a result using a QueryIndexView.  If you wish to '
            'execute a query use the database \'get_query_result\' convenience '
            'method.'
        )
