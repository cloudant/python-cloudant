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
API module for interacting with scheduler endpoints
"""

from ._common_util import response_to_json_dict

class Scheduler(object):
    """
    API for retrieving scheduler jobs and documents.

    :param client: Client instance used by the database.  Can either be a
        ``CouchDB`` or ``Cloudant`` client instance.
    """

    def __init__(self, client):
        self._client = client
        self._r_session = client.r_session
        self._scheduler = '/'.join([self._client.server_url, '_scheduler'])

    def list_docs(self, limit=None, skip=None):
        """
        Lists replication documents. Includes information
        about all the documents, even in completed and failed
        states. For each document it returns the document ID, the
        database, the replication ID, source and target, and other
        information.

        :param limit: How many results to return.
        :param skip: How many result to skip starting at the beginning, if ordered by document ID.
        """
        params = dict()
        if limit is not None:
            params["limit"] = limit
        if skip is not None:
            params["skip"] = skip
        resp = self._r_session.get('/'.join([self._scheduler, 'docs']), params=params)
        resp.raise_for_status()
        return response_to_json_dict(resp)

    def get_doc(self, doc_id):
        """
        Get replication document state for a given replication document ID.
        """
        resp = self._r_session.get('/'.join([self._scheduler, 'docs', '_replicator', doc_id]))
        resp.raise_for_status()
        return response_to_json_dict(resp)


    def list_jobs(self, limit=None, skip=None):
        """
        Lists replication jobs. Includes replications created via
        /_replicate endpoint as well as those created from replication
        documents. Does not include replications which have completed
        or have failed to start because replication documents were
        malformed. Each job description will include source and target
        information, replication id, a history of recent event, and a
        few other things.

        :param limit: How many results to return.
        :param skip: How many result to skip starting at the beginning, if ordered by document ID.
        """
        params = dict()
        if limit is not None:
            params["limit"] = limit
        if skip is not None:
            params["skip"] = skip
        resp = self._r_session.get('/'.join([self._scheduler, 'jobs']), params=params)
        resp.raise_for_status()
        return response_to_json_dict(resp)
