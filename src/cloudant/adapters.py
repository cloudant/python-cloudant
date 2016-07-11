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
"""
Module that contains default transport adapters for use with requests.
"""
from requests.adapters import HTTPAdapter

from requests.packages.urllib3.util import Retry

class Replay429Adapter(HTTPAdapter):
    """
    A requests TransportAdapter that extends the default HTTPAdapter with configuration
    to replay requests that receive a 429 Too Many Requests response from the server.
    The duration of the sleep between requests will be doubled for each 429 response
    received.

    Parameters can be passed in to control behavior:

    :param int retries: the number of times the request can be replayed before failing.
    :param float initialBackoff: time in seconds for the first backoff.
    """
    def __init__(self, retries=3, initialBackoff=0.25):
        super(Replay429Adapter, self).__init__(max_retries=Retry(
            # Configure the number of retries for status codes
            total=retries,
            # No retries for connect|read errors
            connect=0,
            read=0,
            # Allow retries for all the CouchDB HTTP method types
            method_whitelist=frozenset(['GET', 'HEAD', 'PUT', 'POST',
                                        'DELETE', 'COPY']),
            # Only retry for a 429 too many requests status code
            status_forcelist=[429],
            # Configure the start value of the doubling backoff
            backoff_factor=initialBackoff))
