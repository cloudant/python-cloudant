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
Unit tests for `LRUDict` type.
"""
import unittest

from cloudant.lru_dict import LRUDict


class LRUDictTests(unittest.TestCase):

    def _add_keys(self, d, count):
        for i in range(count):
            d['foo-{0}'.format(i)] = 'bar'

    def test_lru_dict_with_max_size_0(self):
        lru = LRUDict(max_size=0)
        self._add_keys(lru, 999)

        self.assertEquals(0, len(lru))

    def test_lru_dict_with_max_size_100(self):
        lru = LRUDict(max_size=100)
        self._add_keys(lru, 999)

        self.assertEquals(100, len(lru))

    def test_lru_removes_least_recently_added(self):
        lru = LRUDict(max_size=5)
        # fill lru
        lru["first"]    = 1
        lru["second"]   = 2
        lru["third"]    = 3
        lru["forth"]    = 4
        lru["fifth"]    = 5

        self.assertEquals(5, len(lru))

        lru["sixth"]    = 6

        self.assertEquals(5, len(lru))
        self.assertTrue("first" not in lru)

    def test_lru_removes_least_recently_accessed(self):
        lru = LRUDict(max_size=5)
        # fill lru
        lru["first"]    = 1
        lru["second"]   = 2
        lru["third"]    = 3
        lru["forth"]    = 4
        lru["fifth"]    = 5

        self.assertEquals(5, len(lru))
        self.assertEquals(1, lru["first"])  # access first

        lru["sixth"]    = 6

        self.assertEquals(5, len(lru))
        self.assertTrue("second" not in lru)
