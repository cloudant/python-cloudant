#!/usr/bin/env python
# Copyright (C) 2018 IBM Corp. All rights reserved.
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
TODO
"""

class Scheduler(object):
    """
    TODO
    """

    def __init__(self, client):
        self._client = client
        self._r_session = client.r_session
        self._scheduler = '/'.join([self._client.server_url, '_scheduler'])

    def list_docs(self, limit=None, skip=None):
        """
        TODO
        """
        params = dict()
        if limit != None:
            params["limit"] = limit
        if skip != None:
            params["skip"] = skip
        resp = self._r_session.get('/'.join([self._scheduler, 'docs']), params=params)
        resp.raise_for_status()
        return resp.json()

    def get_doc(self, doc_id):
        """
        TODO
        """
        resp = self._r_session.get('/'.join([self._scheduler, 'docs', '_replicator', doc_id]))
        resp.raise_for_status()
        return resp.json()


    def list_jobs(self, limit=None, skip=None):
        """
        TODO
        """
        params = dict()
        if limit != None:
            params["limit"] = limit
        if skip != None:
            params["skip"] = skip
        resp = self._r_session.get('/'.join([self._scheduler, 'jobs']), params=params)
        resp.raise_for_status()
        return resp.json()
