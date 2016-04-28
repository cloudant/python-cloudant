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
from .error import CloudantArgumentError, CloudantException
from ._common_util import feed_arg_types, TYPE_CONVERTERS

class Feed(object):
    """
    Provides an iterator for consuming client and database feeds such as
    ``_db_updates`` and ``_changes``.  A Feed object is constructed with a
    :mod:`~cloudant.client` or a :mod:`~cloudant.database` which it uses to
    issue HTTP requests to the appropriate feed endpoint. Instead of using this
    class directly, it is recommended to use the client APIs
    :func:`~cloudant.client.CouchDB.db_updates`,
    :func:`~cloudant.client.Cloudant.db_updates`, or the database API
    :func:`~cloudant.database.CouchDatabase.changes`.  Reference those methods
    for a list of valid feed options.

    :param source: Either a :mod:`~cloudant.client` object or a
        :mod:`~cloudant.database` object.
    :param bool raw_data: If set to True then the raw response data will be
        streamed otherwise if set to False then JSON formatted data will be
        streamed.  Default is False.
    """
    def __init__(self, source, raw_data=False, **options):
        self._r_session = source.r_session
        self._raw_data = raw_data
        self._options = options
        self._source = source.__class__.__name__
        if self._source == 'CouchDB':
            self._url = '/'.join([source.server_url, '_db_updates'])
            # Set CouchDB _db_updates option defaults as they differ from
            # the _changes and Cloudant _db_updates option defaults
            self._options['feed'] = self._options.get('feed', 'longpoll')
            self._options['heartbeat'] = self._options.get('heartbeat', True)
        elif self._source == 'Cloudant':
            self._url = '/'.join([source.server_url, '_db_updates'])
        else:
            self._url = '/'.join([source.database_url, '_changes'])
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
        Perform translation of feed options passed in as keyword
        arguments to CouchDB/Cloudant equivalent.
        """
        translation = dict()
        for key, val in iteritems_(options):
            self._validate(key, val, feed_arg_types(self._source))
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

    def _validate(self, key, val, arg_types):
        """
        Ensures that the key and the value are valid arguments to be used with
        the feed.
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
        if key == 'feed':
            valid_vals = ('continuous', 'normal', 'longpoll')
            if self._source == 'CouchDB':
                valid_vals = ('continuous', 'longpoll')
            if val not in valid_vals:
                msg = (
                    'Invalid value ({0}) for feed option.  Must be one of {1}.'
                ).format(val, valid_vals)
                raise CloudantArgumentError(msg)
        if key == 'style' and val not in ('main_only', 'all_docs'):
            msg = ('Invalid value ({0}) for style option.  Must be main_only, '
                   'or all_docs.').format(val)
            raise CloudantArgumentError(msg)

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
            if (self._options.get('heartbeat', False) and
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

class InfiniteFeed(Feed):
    """
    Provides an infinite iterator for consuming client and database feeds such
    as ``_db_updates`` and ``_changes``.  An InfiniteFeed object is constructed
    with a :class:`~cloudant.client.Cloudant` object or a
    :mod:`~cloudant.database` object which it uses to issue HTTP requests to the
    appropriate feed endpoint.  An infinite feed is NOT supported for use with a
    :class:`~cloudant.client.CouchDB` object and unlike a
    :class:`~cloudant.feed.Feed` which can be a ``normal``, ``longpoll``,
    or ``continuous`` feed, an InfiniteFeed can only be ``continuous`` and the
    iterator will only stream formatted JSON objects.  Instead of using this
    class directly, it is recommended to use the client
    API :func:`~cloudant.client.Cloudant.infinite_db_updates` or the database
    API :func:`~cloudant.database.CouchDatabase._infinite_changes`.  Reference
    those methods for a valid list of feed options.

    Note: The infinite iterator is not exception resilient so if an
    unexpected exception occurs, the iterator will terminate.  Any unexpected
    exceptions should be handled in code outside of this library.  If you wish
    to restart the infinite iterator from where it left off that can be done by
    constructing a new InfiniteFeed object with the ``since`` option set to the
    sequence number of the last row of data prior to termination.

    :param source: Either a :class:`~cloudant.client.Cloudant` object or a
        :mod:`~cloudant.database` object.
    """
    def __init__(self, source, **options):
        super(InfiniteFeed, self).__init__(source, False, **options)
        # Default feed to continuous if not explicitly set
        self._options['feed'] = self._options.get('feed', 'continuous')

    def _validate(self, key, val, arg_types):
        """
        Ensures that the key and the value are valid arguments to be used with
        the feed.
        """
        if key == 'feed' and val != 'continuous':
            msg = (
                'Invalid infinite feed option: {0}.  Must be set to continuous.'
            ).format(val)
            raise CloudantArgumentError(msg)
        super(InfiniteFeed, self)._validate(key, val, arg_types)

    def next(self):
        """
        Handles the iteration by pulling the next line out of the stream and
        converting the response to JSON.

        :returns: Data representing what was seen in the feed
        """
        if self._source == 'CouchDB':
            raise CloudantException(
                'Infinite _db_updates feed not supported for CouchDB.')
        if self._last_seq:
            self._options.update({'since': self._last_seq})
            self._resp = None
            self._last_seq = None
        return super(InfiniteFeed, self).next()
