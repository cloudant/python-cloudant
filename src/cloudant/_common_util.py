#!/usr/bin/env python
# Copyright (C) 2015, 2019 IBM Corp. All rights reserved.
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
import json

from ._2to3 import LONGTYPE, STRTYPE, NONETYPE, UNITYPE, iteritems_
from .error import CloudantArgumentError, CloudantException, CloudantClientException

try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence

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

ANY_ARG = object()
ANY_TYPE = object()

RESULT_ARG_TYPES = {
    'descending': (bool,),
    'endkey': (int, LONGTYPE, STRTYPE, Sequence,),
    'endkey_docid': (STRTYPE,),
    'group': (bool,),
    'group_level': (int, LONGTYPE, NONETYPE,),
    'include_docs': (bool,),
    'inclusive_end': (bool,),
    'key': (int, LONGTYPE, STRTYPE, Sequence,),
    'keys': (list,),
    'limit': (int, LONGTYPE, NONETYPE,),
    'reduce': (bool,),
    'skip': (int, LONGTYPE, NONETYPE,),
    'stable': (bool,),
    'stale': (STRTYPE,),
    'startkey': (int, LONGTYPE, STRTYPE, Sequence,),
    'startkey_docid': (STRTYPE,),
    'update': (STRTYPE,),
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
    LONGTYPE: lambda x: x,
    bool: lambda x: 'true' if x else 'false',
    NONETYPE: lambda x: x
}

_COUCH_DB_UPDATES_ARG_TYPES = {
    'feed': (STRTYPE,),
    'heartbeat': (bool,),
    'timeout': (int, LONGTYPE, NONETYPE,),
}

_DB_UPDATES_ARG_TYPES = {
    'descending': (bool,),
    'limit': (int, LONGTYPE, NONETYPE,),
    'since': (int, LONGTYPE, STRTYPE,),
}
_DB_UPDATES_ARG_TYPES.update(_COUCH_DB_UPDATES_ARG_TYPES)
_DB_UPDATES_ARG_TYPES['heartbeat'] = (int, LONGTYPE, NONETYPE,)

_CHANGES_ARG_TYPES = {
    'conflicts': (bool,),
    'doc_ids': (list,),
    'filter': (STRTYPE,),
    'include_docs': (bool,),
    'style': (STRTYPE,),
    ANY_ARG: ANY_TYPE  # pass arbitrary query parameters to a custom filter
}
_CHANGES_ARG_TYPES.update(_DB_UPDATES_ARG_TYPES)

QUERY_ARG_TYPES = {
    'selector': dict,
    'limit': (int, LONGTYPE, NONETYPE),
    'skip': (int, LONGTYPE, NONETYPE),
    'sort': list,
    'fields': list,
    'r': (int, LONGTYPE, NONETYPE),
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
    'query': (STRTYPE, int, LONGTYPE),
    'q': (STRTYPE, int, LONGTYPE),
    'ranges': dict,
    'sort': (STRTYPE, list),
    'stale': STRTYPE,
    'highlight_fields': list,
    'highlight_pre_tag': STRTYPE,
    'highlight_post_tag': STRTYPE,
    'highlight_number': (int, LONGTYPE, NONETYPE),
    'highlight_size': (int, LONGTYPE, NONETYPE),
    'include_fields': list,
    'partition': STRTYPE
}

# Functions

def feed_arg_types(feed_type):
    """
    Return the appropriate argument type dictionary based on the type of feed.
    """
    if feed_type == 'Cloudant':
        return _DB_UPDATES_ARG_TYPES
    if feed_type == 'CouchDB':
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
        raise CloudantArgumentError(116, key)
    # pylint: disable=unidiomatic-typecheck
    # Validate argument values and ensure that a boolean is not passed in
    # if an integer is expected
    if (not isinstance(val, RESULT_ARG_TYPES[key]) or
            (type(val) is bool and int in RESULT_ARG_TYPES[key])):
        raise CloudantArgumentError(117, key, RESULT_ARG_TYPES[key])
    if key == 'keys':
        for key_list_val in val:
            if (not isinstance(key_list_val, RESULT_ARG_TYPES['key']) or
                    type(key_list_val) is bool):
                raise CloudantArgumentError(134, RESULT_ARG_TYPES['key'])
    if key == 'stale':
        if val not in ('ok', 'update_after'):
            raise CloudantArgumentError(135, val)

def _py_to_couch_translate(key, val):
    """
    Performs the conversion of the Python parameter value to its CouchDB
    equivalent.
    """
    try:
        if key in ['keys', 'endkey_docid', 'startkey_docid', 'stale', 'update']:
            return {key: val}
        if val is None:
            return {key: None}
        arg_converter = TYPE_CONVERTERS.get(type(val))
        return {key: arg_converter(val)}
    except Exception as ex:
        raise CloudantArgumentError(136, key, ex)

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
    if keys_list is not None:
        keys = json.dumps({'keys': keys_list}, cls=encoder)
    f_params = python_to_couch(params)
    resp = None
    if keys is not None:
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
    Provides a helper to act as callback function for the response event hook
    and add a HTTP response error with reason message to ``response.reason``.
    The ``response`` and ``**kwargs`` are necessary for this function to
    properly operate as the callback.

    :param response: HTTP response object
    :param kwargs: HTTP request parameters
    """
    if response.status_code >= 400:
        try:
            resp_dict = response_to_json_dict(response)
            error = resp_dict.get('error', '')
            reason = resp_dict.get('reason', '')
            # Append to the existing response's reason
            response.reason += ' {0} {1}'.format(error, reason)
        except ValueError:
            pass
    return response

def response_to_json_dict(response, **kwargs):
    """
    Standard place to convert responses to JSON.

    :param response: requests response object
    :param **kwargs: arguments accepted by json.loads

    :returns: dict of JSON response
    """
    if response.encoding is None:
        response.encoding = 'utf-8'
    return json.loads(response.text, **kwargs)

# Classes


class _Code(str):
    """
    Wraps a ``str`` object as a _Code object providing the means to handle
    Javascript blob content.  Used internally by the View object when
    codifying map and reduce Javascript content.
    """
    def __new__(cls, code):
        if type(code).__name__ == 'unicode':
            return str.__new__(cls, code.encode('utf8'))
        return str.__new__(cls, code)


class CloudFoundryService(object):
    """ Manages Cloud Foundry service configuration. """

    def __init__(self, vcap_services, instance_name=None, service_name=None):
        try:
            services = vcap_services
            if not isinstance(vcap_services, dict):
                services = json.loads(vcap_services)

            cloudant_services = services.get(service_name, [])

            # use first service if no name given and only one service present
            use_first = instance_name is None and len(cloudant_services) == 1
            for service in cloudant_services:
                if use_first or service.get('name') == instance_name:
                    credentials = service['credentials']
                    self._host = credentials['host']
                    self._name = service.get('name')
                    self._port = credentials.get('port', 443)
                    self._username = credentials['username']
                    if 'apikey' in credentials:
                        self._iam_api_key = credentials['apikey']
                    elif 'username' in credentials and 'password' in credentials:
                        self._password = credentials['password']
                    else:
                        raise CloudantClientException(103)
                    break
            else:
                raise CloudantException('Missing service in VCAP_SERVICES')

        except KeyError as ex:
            raise CloudantException(
                "Invalid service: '{0}' missing".format(ex.args[0])
            )

        except TypeError:
            raise CloudantException(
                'Failed to decode VCAP_SERVICES service credentials'
            )

        except ValueError:
            raise CloudantException('Failed to decode VCAP_SERVICES JSON')

    @property
    def host(self):
        """ Return service host. """
        return self._host

    @property
    def name(self):
        """ Return service name. """
        return self._name

    @property
    def password(self):
        """ Return service password. """
        return self._password

    @property
    def port(self):
        """ Return service port. """
        return str(self._port)

    @property
    def url(self):
        """ Return service url. """
        return 'https://{0}:{1}'.format(self._host, self._port)

    @property
    def username(self):
        """ Return service username. """
        return self._username

    @property
    def iam_api_key(self):
        """ Return service IAM API key. """
        return self._iam_api_key
