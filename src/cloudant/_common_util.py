#!/usr/bin/env python
# Copyright (c) 2015, 2016 IBM. All rights reserved.
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
Module containing miscellaneous classes, functions, and constants used
throughout the library.
"""

import sys
import platform
from collections import Sequence
import json

from ._2to3 import STRTYPE, NONETYPE, UNITYPE, iteritems_
from .error import CloudantArgumentError

# Library Constants

USER_AGENT = '/'.join([
    'python-cloudant',
    sys.modules['cloudant'].__version__,
    'Python',
    '{0}.{1}.{2}'.format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]),
    platform.system(),
    platform.machine()
])

QUERY_LANGUAGE = 'query'

# Index Types

JSON_INDEX_TYPE = 'json'
TEXT_INDEX_TYPE = 'text'
SPECIAL_INDEX_TYPE = 'special'

# Argument Types

RESULT_ARG_TYPES = {
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

_COUCH_DB_UPDATES_ARG_TYPES = {
    'feed': (STRTYPE,),
    'heartbeat': (bool,),
    'timeout': (int, NONETYPE,),
}

_DB_UPDATES_ARG_TYPES = {
    'descending': (bool,),
    'limit': (int, NONETYPE,),
    'since': (int, STRTYPE,),
}
_DB_UPDATES_ARG_TYPES.update(_COUCH_DB_UPDATES_ARG_TYPES)
_DB_UPDATES_ARG_TYPES['heartbeat'] = (int, NONETYPE,)

_CHANGES_ARG_TYPES = {
    'conflicts': (bool,),
    'doc_ids': (list,),
    'filter': (STRTYPE,),
    'include_docs': (bool,),
    'style': (STRTYPE,),
}
_CHANGES_ARG_TYPES.update(_DB_UPDATES_ARG_TYPES)

QUERY_ARG_TYPES = {
    'selector': dict,
    'limit': (int, NONETYPE),
    'skip': (int, NONETYPE),
    'sort': list,
    'fields': list,
    'r': (int, NONETYPE),
    'bookmark': STRTYPE,
    'use_index': STRTYPE
}

TEXT_INDEX_ARGS = {'fields': list, 'default_field': dict, 'selector': dict}

SEARCH_INDEX_ARGS = {
    'bookmark': STRTYPE,
    'counts': list,
    'drilldown': list,
    'group_field': STRTYPE,
    'group_limit': (int, NONETYPE),
    'group_sort': (STRTYPE, list),
    'include_docs': bool,
    'limit': (int, NONETYPE),
    'query': (STRTYPE, int),
    'q': (STRTYPE, int),
    'ranges': dict,
    'sort': (STRTYPE, list),
    'stale': STRTYPE,
    'highlight_fields': list,
    'highlight_pre_tag': STRTYPE,
    'highlight_post_tag': STRTYPE,
    'highlight_number': (int, NONETYPE),
    'highlight_size': (int, NONETYPE),
    'include_fields': list
}

# Functions

def feed_arg_types(feed_type):
    """
    Return the appropriate argument type dictionary based on the type of feed.
    """
    if feed_type == 'Cloudant':
        return _DB_UPDATES_ARG_TYPES
    elif feed_type == 'CouchDB':
        return _COUCH_DB_UPDATES_ARG_TYPES
    return _CHANGES_ARG_TYPES

def python_to_couch(options):
    """
    Translates query options from python style options into CouchDB/Cloudant
    query options.  For example ``{'include_docs': True}`` will
    translate to ``{'include_docs': 'true'}``.  Primarily meant for use by
    code that formulates a query to retrieve results data from the
    remote database, such as the database API convenience method
    :func:`~cloudant.database.CouchDatabase.all_docs` or the View
    :func:`~cloudant.view.View.__call__` callable, both used to retrieve data.

    :param dict options: Python style parameters to be translated.

    :returns: Dictionary of translated CouchDB/Cloudant query parameters
    """
    translation = dict()
    for key, val in iteritems_(options):
        py_to_couch_validate(key, val)
        translation.update(_py_to_couch_translate(key, val))
    return translation

def py_to_couch_validate(key, val):
    """
    Validates the individual parameter key and value.
    """
    if key not in RESULT_ARG_TYPES:
        msg = 'Invalid argument {0}'.format(key)
        raise CloudantArgumentError(msg)
    # pylint: disable=unidiomatic-typecheck
    # Validate argument values and ensure that a boolean is not passed in
    # if an integer is expected
    if (not isinstance(val, RESULT_ARG_TYPES[key]) or
            (type(val) is bool and int in RESULT_ARG_TYPES[key])):
        msg = 'Argument {0} not instance of expected type: {1}'.format(
            key,
            RESULT_ARG_TYPES[key]
        )
        raise CloudantArgumentError(msg)
    if key == 'keys':
        for key_list_val in val:
            if (not isinstance(key_list_val, RESULT_ARG_TYPES['key']) or
                    type(key_list_val) is bool):
                msg = 'Key list element not of expected type: {0}'.format(
                    RESULT_ARG_TYPES['key']
                )
                raise CloudantArgumentError(msg)
    if key == 'stale':
        if val not in ('ok', 'update_after'):
            msg = (
                'Invalid value for stale option {0} '
                'must be ok or update_after'
            ).format(val)
            raise CloudantArgumentError(msg)

def _py_to_couch_translate(key, val):
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

def codify(code_or_str):
    """
    Provides a helper to rationalize code content.
    """
    if code_or_str is None:
        return None
    if not isinstance(code_or_str, _Code):
        return _Code(code_or_str)
    return code_or_str

def get_docs(r_session, url, encoder=None, headers=None, **params):
    """
    Provides a helper for functions that require GET or POST requests
    with a JSON, text, or raw response containing documents.

    :param r_session: Authentication session from the client
    :param str url: URL containing the endpoint
    :param JSONEncoder encoder: Custom encoder from the client
    :param dict headers: Optional HTTP Headers to send with the request

    :returns: Raw response content from the specified endpoint
    """
    keys_list = params.pop('keys', None)
    keys = None
    if keys_list:
        keys = json.dumps({'keys': keys_list}, cls=encoder)
    f_params = python_to_couch(params)
    resp = None
    if keys:
        # If we're using POST we are sending JSON so add the header
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'application/json'
        resp = r_session.post(url, headers=headers, params=f_params, data=keys)
    else:
        resp = r_session.get(url, headers=headers, params=f_params)
    resp.raise_for_status()
    return resp

#pylint: disable=unused-argument
def append_response_error_content(response, **kwargs):
    """
    Provides a helper to add HTTP response error and reason messages.
    """
    try:
        if response.status_code >= 400 and response.json():
            reason = response.json().pop('reason', None)
            error = response.json().pop('error', None)
            response.reason += ' %s %s' % (error, reason)
            return response
    except ValueError:
        return

# Classes

class _Code(str):
    """
    Wraps a ``str`` object as a _Code object providing the means to handle
    Javascript blob content.  Used internally by the View object when
    codifying map and reduce Javascript content.
    """
    def __new__(cls, code):
        return str.__new__(cls, code)
