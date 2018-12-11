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
_database_partition_tests_
"""

import unittest
import mock

from cloudant.client import Cloudant


class DatabasePartitionTests(unittest.TestCase):

    def __init__(self, *arg, **kwargs):
        super(DatabasePartitionTests, self).__init__(*arg, **kwargs)

        self.client = Cloudant('foo', 'bar', account='foo', use_basic_auth=True)
        self.client.connect()

        self.mock_200 = mock.MagicMock()
        type(self.mock_200).status_code = mock.PropertyMock(return_value=200)
        self.mock_200.json.return_value = {'ok': True}

        self.mock_404 = mock.MagicMock()
        type(self.mock_404).status_code = mock.PropertyMock(return_value=404)
        self.mock_404.json.return_value = {'error': 'missing'}

        self.mock_empty_results = mock.MagicMock()
        type(self.mock_200).status_code = mock.PropertyMock(return_value=200)
        self.mock_200.json.return_value = {'docs': []}

    @mock.patch('cloudant._client_session.ClientSession.request')
    def test_create_partitioned_database(self, m_req):
        m_req.side_effect = [self.mock_404, self.mock_200]

        db = self.client.create_database('partitioned_db_1', partitioned=True)
        self.assertTrue(db.partitioned)

        self.assertEquals(m_req.call_count, 2)

        m_req.assert_has_calls([
            mock.call('HEAD', 'https://foo.cloudant.com/partitioned_db_1',
                      allow_redirects=False, auth=('foo', 'bar')),
            mock.call('PUT', 'https://foo.cloudant.com/partitioned_db_1',
                      auth=('foo', 'bar'), data=None,
                      params={'partitioned': 'true'})
        ])

    @mock.patch('cloudant._client_session.ClientSession.request')
    def test_database_partition_query(self, m_req):
        m_req.side_effects = [
            self.mock_404,
            self.mock_200,
            self.mock_empty_results
        ]

        db = self.client.create_database('partitioned_db_2', partitioned=True)
        self.assertTrue(db.partitioned)

        result = db.partition('partition_key_a')\
                   .query(selector={'name': {'$eq': 'foo'}})

        docs = [doc for doc in result]  # trigger query fetch
        self.assertEquals(len(docs), 0)

        self.assertEquals(m_req.call_count, 3)

        calls = [
            mock.call('HEAD', 'https://foo.cloudant.com/partitioned_db_2',
                      allow_redirects=False, auth=('foo', 'bar')),
            mock.call('PUT', 'https://foo.cloudant.com/partitioned_db_2',
                      auth=('foo', 'bar'), data=None,
                      params={'partitioned': 'true'}),
            mock.call('POST',
                      'https://foo.cloudant.com/partitioned_db_2/_partition/partition_key_a/_find',
                      auth=('foo', 'bar'),
                      data='{"skip": 0, "limit": 100, "selector": {"name": {"$eq": "foo"}}}',
                      headers={'Content-Type': 'application/json'}, json=None)
        ]

        self.assertTrue(all([call in m_req.call_args_list for call in calls]))

    @mock.patch('cloudant._client_session.ClientSession.request')
    def test_database_partition_search(self, m_req):
        m_req.side_effects = [
            self.mock_404,
            self.mock_200,
            self.mock_empty_results
        ]

        db = self.client.create_database('partitioned_db_3', partitioned=True)
        self.assertTrue(db.partitioned)

        result = db.partition('partition_key_b')\
                   .search('ddoc001', 'searchindex001', query='name:julia*')

        docs = [doc for doc in result]  # trigger query fetch
        self.assertEquals(len(docs), 0)

        self.assertEquals(m_req.call_count, 3)

        calls = [
            mock.call('HEAD', 'https://foo.cloudant.com/partitioned_db_3',
                      allow_redirects=False, auth=('foo', 'bar')),
            mock.call('PUT', 'https://foo.cloudant.com/partitioned_db_3',
                      auth=('foo', 'bar'), data=None,
                      params={'partitioned': 'true'}),
            mock.call('POST',
                      'https://foo.cloudant.com/partitioned_db_3/_partition/partition_key_b/_design/ddoc001/_search/searchindex001',
                      auth=('foo', 'bar'), data='{"query": "name:julia*"}',
                      headers={'Content-Type': 'application/json'}, json=None)
        ]

        self.assertTrue(all([call in m_req.call_args_list for call in calls]))

    @mock.patch('cloudant._client_session.ClientSession.request')
    def test_database_partition_view(self, m_req):
        m_req.side_effects = [
            self.mock_404,
            self.mock_200,
            self.mock_empty_results
        ]

        db = self.client.create_database('partitioned_db_4', partitioned=True)
        self.assertTrue(db.partitioned)

        result = db.partition('partition_key_c')\
                   .view('ddoc', 'my_view')

        docs = [doc for doc in result]  # trigger query fetch
        self.assertEquals(len(docs), 0)

        self.assertEquals(m_req.call_count, 3)

        calls = [
            mock.call('HEAD', 'https://foo.cloudant.com/partitioned_db_4',
                      allow_redirects=False, auth=('foo', 'bar')),
            mock.call('PUT', 'https://foo.cloudant.com/partitioned_db_4',
                      auth=('foo', 'bar'), data=None,
                      params={'partitioned': 'true'}),
            mock.call('GET',
                      'https://foo.cloudant.com/partitioned_db_4/_partition/partition_key_c/_design/ddoc/_view/my_view',
                      allow_redirects=True, auth=('foo', 'bar'), headers=None,
                      params={'skip': 0, 'limit': 100})
        ]

        self.assertTrue(all([call in m_req.call_args_list for call in calls]))
