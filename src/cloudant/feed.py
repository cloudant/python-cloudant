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
Module containing the Feed class which provides iterator support for consuming
continuous and non-continuous feeds like ``_changes`` and ``_db_updates``.
"""

import json

from ._2to3 import iteritems_, next_, unicode_, STRTYPE, NONETYPE
from .result import TYPE_CONVERTERS
from .error import CloudantArgumentError, CloudantException

_DB_UPDATES_ARG_TYPES = {
    'descending': (bool,),
    'feed': (STRTYPE,),
    'heartbeat': (int, NONETYPE,),
    'limit': (int, NONETYPE,),
    'since': (int, STRTYPE,),
    'timeout': (int, NONETYPE,),
}

_CHANGES_ARG_TYPES = {
    'conflicts': (bool,),
    'doc_ids': (list,),
    'filter': (STRTYPE,),
    'include_docs': (bool,),
    'style': (STRTYPE,),
}
_CHANGES_ARG_TYPES.update(_DB_UPDATES_ARG_TYPES)

def _validate(key, val, arg_types):
    """
    Ensures that the key and the value are valid arguments to be used with the
    feed.
    """
    if key not in arg_types:
        raise CloudantArgumentError('Invalid argument {0}'.format(key))
    if (not isinstance(val, arg_types[key]) or
            (isinstance(val, bool) and int in arg_types[key])):
        msg = 'Argument {0} not instance of expected type: {1}'.format(
            key, arg_types[key])
        raise CloudantArgumentError(msg)
    if isinstance(val, int) and val <= 0 and not isinstance(val, bool):
        msg = 'Argument {0} must be > 0.  Found: {1}'.format(key, val)
        raise CloudantArgumentError(msg)
    if key == 'feed' and val not in ('continuous', 'normal', 'longpoll'):
        msg = ('Invalid value ({0}) for feed option.  Must be continuous, '
               'normal, or longpoll.').format(val)
        raise CloudantArgumentError(msg)
    if key == 'style' and val not in ('main_only', 'all_docs'):
        msg = ('Invalid value ({0}) for style option.  Must be main_only, '
               'or all_docs.').format(val)
        raise CloudantArgumentError(msg)

class Feed(object):
    """
    Provides an iterator for consuming client and database feeds such as
    ``_db_updates`` and ``_changes``.  A Feed object is constructed with a
    reference to a client or database Requests Session object and a feed
    endpoint URL. Instead of using this class directly, it is recommended to
    use the client API :func:`~cloudant.client.CouchDB.db_updates` and the
    database API :func:`~cloudant.database.CouchDatabase.changes`.  Reference
    those methods for a valid list of feed options.

    :param Session session: Requests session used by the Feed.
    :param str url: URL used by the Feed.
    :param bool raw_data: Dictates whether the streamed data is returned as
        a decoded Python ``dict`` object or as raw response data.  Defaults to
        False.
    """
    def __init__(self, session, url, raw_data=False, **options):
        self._r_session = session
        self._url = url
        self._raw_data = raw_data
        self._options = options
        self._chunk_size = self._options.pop('chunk_size', 512)

        self._resp = None
        self._lines = None
        self._last_seq = None
        self._stop = False

    @property
    def last_seq(self):
        """
        Returns the last sequence identifier for the feed.  Only available after
        the feed has iterated through to completion.

        :returns: A string representing the last sequence number of a feed.
        """
        return self._last_seq

    def stop(self):
        """
        Stops a feed iteration.
        """
        self._stop = True

    def _start(self):
        """
        Starts streaming the feed using the provided session and feed options.
        """
        params = self._translate(self._options)
        self._resp = self._r_session.get(self._url, params=params, stream=True)
        self._resp.raise_for_status()
        self._lines = self._resp.iter_lines(self._chunk_size)

    def _translate(self, options):
        """
        Perform translation to CouchDB of feed options passed in as keyword
        arguments.
        """
        if self._url.endswith('/_changes'):
            arg_types = _CHANGES_ARG_TYPES
        elif self._url.endswith('/_db_updates'):
            arg_types = _DB_UPDATES_ARG_TYPES
        else:
            msg = 'Could not identify feed based on url: {0}'.format(self._url)
            raise CloudantException(msg)
        translation = dict()
        for key, val in iteritems_(options):
            _validate(key, val, arg_types)
            try:
                if isinstance(val, STRTYPE):
                    translation[key] = val
                elif not isinstance(val, NONETYPE):
                    arg_converter = TYPE_CONVERTERS.get(type(val))
                    translation[key] = arg_converter(val)
            except Exception as ex:
                msg = 'Error converting argument {0}: {1}'.format(key, ex)
                raise CloudantArgumentError(msg)
        return translation

    def __iter__(self):
        """
        Makes this object an iterator.
        """
        return self

    def __next__(self):
        """
        Provides Python3 compatibility.
        """
        return self.next()

    def next(self):
        """
        Handles the iteration by pulling the next line out of the stream,
        attempting to convert the response to JSON if necessary.

        :returns: Data representing what was seen in the feed
        """
        if not self._resp:
            self._start()
        if self._stop:
            raise StopIteration
        skip, data = self._process_data(next_(self._lines))
        if skip:
            return self.next()
        return data

    def _process_data(self, line):
        """
        Validates and processes the line passed in and converts it to a
        Python object if necessary.
        """
        skip = False
        if self._raw_data:
            return skip, line
        else:
            line = unicode_(line)
        if not line:
            if ('heartbeat' in self._options and
                    self._options.get('feed') in ('continuous', 'longpoll') and
                    not self._last_seq):
                line = None
            else:
                skip = True
        elif line in ('{"results":[', '],'):
            skip = True
        elif line[-1] == ',':
            line = line[:-1]
        elif line[:10] == ('"last_seq"'):
            line = '{' + line
        try:
            if line:
                data = json.loads(line)
                if data.get('last_seq'):
                    self._last_seq = data['last_seq']
                    skip = True
            else:
                data = None
        except ValueError:
            data = {"error": "Bad JSON line", "line": line}
        return skip, data
