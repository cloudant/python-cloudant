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
_feeds_

Iterator support for consuming changes-like feeds

"""

import json


class Feed(object):
    """
    _Feed_

    Acts as an infinite iterator for consuming database feeds such as
    _changes, suitable for feeding a daemon.

    :params:

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
        _start_

        Using the provided session, start streaming
        the feed continuously,
        if a last seq value is present, pass that along.

        """
        params = self._params
        if self._last_seq is not None:
            params['since'] = self._last_seq
        self._resp = self._session.get(self._url, params=params, stream=True)
        self._resp.raise_for_status()
        self._line_iter = self._resp.iter_lines()

    def __iter__(self):
        """
        make this object an iterator
        """
        return self

    def __next__(self):
        """python3 compat"""
        return self.next()

    def next(self):
        """
        _next_

        Iterate: pull next line out of the stream,
        attempt to convert the response to JSON, handling
        case of empty lines.
        If end of feed is seen, restart iterator

        Returns JSON data representing what was seen in the feed.

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
