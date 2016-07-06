#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2016 IBM Corp. All rights reserved.
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
from cloudant.client import CouchDB
from cloudant.adapters import Replay429Adapter
from requests.packages.urllib3.util import Retry
from .unit_t_db_base import UnitTestDbBase

class AdapterTests(UnitTestDbBase):
    """
    Unit tests for transport adapters
    """

    def test_new_Replay429Adapter(self):
        """
        Test that a new Replay429Adapter is accepted as a parameter for a client.
        """
        self.client = CouchDB(
            self.user,
            self.pwd,
            url=self.url,
            adapter=Replay429Adapter())

    def test_retries_arg_Replay429Adapter(self):
        """
        Test constructing a new Replay429Adapter with a configured number of retries.
        """
        self.client = CouchDB(
            self.user,
            self.pwd,
            url=self.url,
            adapter=Replay429Adapter(retries=10))



    def test_backoff_arg_Replay429Adapter(self):
        """
        Test constructing a new Replay429Adapter with a configured initial backoff.
        """
        self.client = CouchDB(
            self.user,
            self.pwd,
            url=self.url,
            adapter=Replay429Adapter(initialBackoff=0.1))

    def test_args_Replay429Adapter(self):
        """
        Test constructing a new Replay429Adapter with configured retries and initial backoff.
        """
        self.client = CouchDB(
            self.user,
            self.pwd,
            url=self.url,
            adapter=Replay429Adapter(retries=10, initialBackoff=0.01))