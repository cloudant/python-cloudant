#!/usr/bin/env python
# Copyright (c) 2017 IBM. All rights reserved.
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
A simple `dict` like collection implementing a Least Recently Used (LRU)
caching policy.
"""

from collections import MutableMapping, OrderedDict
from threading import Lock


class NullContext(object):
    """
    No-op context manager, executes block without doing any additional
    processing.
    """
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class LRUDict(MutableMapping):
    """
    A fixed size `dict` like container which evicts Least Recently Used (LRU)
    items once size limit is exceeded.

    :param int max_size: Maximum size of dictionary. A negative value
        implies the capacity is unbounded.
    """
    def __init__(self, *args, **kwargs):
        self._max_size = kwargs.pop('max_size', -1)

        if self._max_size <= 0:
            self._lock = NullContext()  # don't lock for get/set/delete
        else:
            self._lock = Lock()

        self._dict = OrderedDict(*args, **kwargs)

    def __delitem__(self, key):
        with self._lock:
            self._dict.__getitem__(key).delete()

    def __getitem__(self, key):
        with self._lock:
            value = self._dict.__getitem__(key)
            if self._max_size > 1:
                self._update_lru(key)

            return value

    def _update_lru(self, key):
        """
        Move key to the top of the LRU cache.

        :param str key: dictionary key
        """
        move_to_end = getattr(self._dict, 'move_to_end', None)
        if move_to_end:
            move_to_end(key, last=True)  # >=Python3.2 only
        else:
            # ported from Python3.2
            link_prev, link_next, key = link = \
                getattr(self._dict, '_OrderedDict__map')[key]
            link_prev[1] = link_next
            link_next[0] = link_prev

            root = getattr(self._dict, '_OrderedDict__root')
            last = root[0]
            link[0] = last
            link[1] = root
            last[1] = root[0] = link

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return len(self._dict)

    def __setitem__(self, *args, **kwargs):
        if self._max_size == 0:
            return  # skip set

        with self._lock:
            if 0 < self._max_size <= len(self._dict):
                self._dict.popitem(last=False)

            self._dict.__setitem__(*args, **kwargs)

    def keys(self):
        """
        Return a copy of the dictionary keys.

        :return: list of dictionary keys
        """
        return self._dict.keys()  # override inherited Mapping method
