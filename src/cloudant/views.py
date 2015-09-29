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
_views_

Utilities for handling design docs and the resulting views they create

"""
import contextlib
import posixpath

from .result import Result, python_to_couch


class Code(str):
    """
    _Code_

    string derived object that allows us to wrap/manipulate javascript blobs

    """
    def __init__(self, s):
        super(Code, self).__init__(s)


def _codify(code_or_str):
    """
    helper to rationalise None, str or Code objects
    """
    if code_or_str is None:
        return None
    if not isinstance(code_or_str, Code):
        return Code(code_or_str)
    return code_or_str


class View(dict):
    """
    Dictionary based object representing a view, exposing the map, reduce
    functions as attributes and supporting query/data access via the view

    Provides a sliceable and iterable default result collection that can
    be used to query the view data via the result attribute.

    Eg:

    Using integers to skip/limit:
    view.result[100:200]
    view.result[:200]
    view.result[100:]

    Using strings or lists as startkey/endkey:

    view.result[ ["2013","10"]:["2013","11"] ]
    view.result[["2013","10"]]
    view.result[["2013","10"]:]

    For large views, iteration is supported via result:

    for doc in view.result:
        print doc

    The default result collection provides basic functionality,
    which can be customised with other arguments to the view URL
    using the custom_result context.

    For example:

    #including documents
    with view.custom_result(include_docs=True) as rslt:
        rslt[100:200] # slice by result
        rslt[["2013","10"]:["2013","11"]] # slice by startkey/endkey

        #iteration
        for doc in rslt:
            print doc

    Iteration over a view within startkey/endkey range:

    with view.custom_result(startkey="2013", endkey="2014") as rslt:
        for doc in rslt:
            print doc

    """
    def __init__(self, ddoc, view_name, map_func=None, reduce_func=None):
        super(View, self).__init__()
        self.design_doc = ddoc
        self._r_session = self.design_doc.r_session
        self.view_name = view_name
        if map_func is not None:
            self['map'] = _codify(map_func)
        if reduce_func is not None:
            self['reduce'] = _codify(reduce_func)
        self.result = Result(self)

    @property
    def map(self):
        """map property getter"""
        return self.get('map')

    @map.setter
    def map(self, js_func):
        """map property setter, accepts str or Code obj"""
        self['map'] = _codify(js_func)

    @property
    def reduce(self):
        """reduce property getter"""
        return self.get('reduce')

    @reduce.setter
    def reduce(self, js_func):
        """reduce property setter, accepts str or Code obj"""
        self['reduce'] = _codify(js_func)

    @property
    def url(self):
        """property that builds the view URL"""
        return posixpath.join(
            self.design_doc.document_url,
            '_view',
            self.view_name
        )

    def __call__(self, **kwargs):
        """
        retrieve data from the view, using the kwargs provided
        as query parameters

        descending bool
        endkey string or array
        endkey_docid  string
        group bool
        group_level ??
        include_docs bool
        inclusive_end  bool
        key string
        limit   int
        reduce  boolean
        skip    int
        stale   enum(ok, update_after)
        startkey  string or array
        startkey_docid  string

        """
        params = python_to_couch(kwargs)
        resp = self._r_session.get(self.url, params=params)
        resp.raise_for_status()
        return resp.json()

    def make_result(self, **options):
        """
        Wrap the call to get result data in a Result object.

        """
        return Result(self, **options)

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        _custom_result_

        If you want to customise the result behaviour,
        you can build your own with extra options to the result
        call using this context manager.

        Example:

        with view.custom_result(include_docs=True, reduce=False) as rslt:
            data = rslt[100:200]

        """
        rslt = self.make_result(**options)
        yield rslt
        del rslt
