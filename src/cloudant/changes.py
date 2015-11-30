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
Module containing the Feed class which provides iterator support for consuming
changes-like feeds.
"""

import json

class Feed(object):
    """
    Provides an infinite iterator for consuming database feeds such as
    ``_changes`` and ``_db_updates``, suitable for feeding a daemon.  A Feed
    object is instantiated with a reference to a client's Session object and a
    feed endpoint URL.  Instead of using this class directly, it is recommended
    to use the client API :func:`~cloudant.account.CouchDB.db_updates`
    convenience method for interacting with a client's ``_db_updates`` feed
    and the database API :func:`~cloudant.database.CouchDatabase.changes`
    convenience method for interacting with a database's ``_changes`` feed.

    :param Session session: Client session used by the Feed.
    :param str url: URL used by the Feed.
    :param bool include_docs: If set to True, documents will be returned as
        part of the iteration.  Documents will be returned in JSON format and
        not wrapped as a :class:`~cloudant.document.Document`.  Defaults to
        False.
    :param str since: Feed streaming starts from this sequence identifier.
    :param bool continuous: Dictates the streaming of data.
        Defaults to False.
    """
    def __init__(self, session, url, include_docs=False, **kwargs):
        self._session = session
        self._url = url
        self._resp = None
        self._line_iter = None
        self._last_seq = kwargs.get('since')
        self._continuous = kwargs.get('continuous', False)
        self._end_of_iteration = False
        self._params = {'feed': 'continuous'}
        if include_docs:
            self._params['include_docs'] = 'true'

    def start(self):
        """
        Starts streaming the feed using the provided session.  If a last
        sequence identifier value was provided during instantiation then that
        is used by the Feed as a starting point.
        """
        params = self._params
        if self._last_seq is not None:
            params['since'] = self._last_seq
        self._resp = self._session.get(self._url, params=params, stream=True)
        self._resp.raise_for_status()
        self._line_iter = self._resp.iter_lines()

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
        attempting to convert the response to JSON, and managing empty lines.
        If the end of feed is encountered, the iterator is restarted.

        :returns: Data representing what was seen in the feed in JSON format

        """
        if self._end_of_iteration:
            raise StopIteration
        if not self._resp:
            self.start()
        line = self._line_iter.next()
        if len(line.strip()) == 0:
            return {}
        try:
            data = json.loads(line)
        except ValueError:
            data = {"error": "Bad JSON line", "line": line}

        if data.get('last_seq'):
            if self._continuous:
                # forever mode => restart
                self._last_seq = data['last_seq']
                self.start()
                return {}
            else:
                # not forever mode => break
                return data
        return data
