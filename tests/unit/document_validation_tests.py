#!/usr/bin/env python
# Copyright © 2021 IBM Corp. All rights reserved.
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
import unittest
from enum import Enum
from unittest.mock import Mock, patch

from mock import create_autospec

import requests
from urllib.parse import urlparse

from cloudant import database
from cloudant.design_document import DesignDocument
from cloudant.document import Document
from cloudant.error import CloudantArgumentError

class ValidationExceptionMsg(Enum):
    DOC = 'Invalid document ID:'
    ATTACHMENT = 'Invalid attachment name:'

class Expect(Enum):
    VALIDATION_EXCEPTION_DOCID = CloudantArgumentError(137, '')
    VALIDATION_EXCEPTION_ATT = CloudantArgumentError(138, '')
    RESPONSE_404 = 404
    RESPONSE_200 = 200
    RESPONSE_201 = 201


class ValidationTests(unittest.TestCase):
    """
    Document validation unit tests
    """
    def setUp(self):
        self.doc_r_session_patcher = patch('cloudant.document.Document.r_session')
        self.requests_get_patcher = patch('requests.get')

        self.addCleanup(patch.stopall)

        self.doc_r_session_mock = self.doc_r_session_patcher.start()
        self.requests_get_mock = self.requests_get_patcher.start()

        self.db = create_autospec(database)
        self.db.client = Mock()
        self.db.client.server_url = 'http://mocked.url.com'
        self.db.database_url = 'http://mocked.url.com/my_db'
        self.db.database_name = 'mydb'

    def teardown(self):
        self.addCleanup(patch.stopall)
        del self.db
        del self.doc_r_session_patcher
        del self.requests_get_patcher
        del self.doc_r_session_mock
        del self.requests_get_mock

    # GET and HEAD _all_docs
    # EXPECTED: validation failure
    def test_get_invalid_all_docs(self):
        """
        Test GET/HEAD request for invalid '_all_docs' document ID
        """
        self.get_document_variants('_all_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _design/foo
    # EXPECTED: 200
    def test_get_valid_ddoc(self):
        """
        Test GET/HEAD request for valid '_design/foo' document ID
        """
        self.get_document_variants('_design/foo', Expect.RESPONSE_200.value, path_segment_count=3)
        self.get_document_variants('_design/foo', Expect.RESPONSE_200.value, True, path_segment_count=3)

    # GET and HEAD _design
    # EXPECTED: Validation exception
    def test_get_invalid_design(self):
        """
        Test GET/HEAD request for invalid '_design' document ID
        """
        self.get_document_variants('_design', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_document_variants('_design', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # GET and HEAD /_design/foo with a slash
    # EXPECTED: 404
    def test_get_missing_ddoc_with_slash(self):
        """
        Test GET/HEAD request for missing '/_design/foo' document ID
        """
        self.get_document_variants('/_design/foo', Expect.RESPONSE_404.value, path_segment_count=2)

    # GET and HEAD _design/foo/_view/bar
    # EXPECTED: 404
    def test_get_invalid_view(self):
        """
        Test GET/HEAD request for missing '_design/foo' document ID
        """
        self.get_document_variants('_design/foo/_view/bar', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_view/bar', Expect.RESPONSE_404.value, True, path_segment_count=3)

    # GET and HEAD _design/foo/_info
    # EXPECTED: 404
    def test_get_invalid_view_info(self):
        """
        Test GET/HEAD request for missing '_design/foo/_info' document ID
        """
        self.get_document_variants('_design/foo/_info', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_info', Expect.RESPONSE_404.value, True, path_segment_count=3)

    # GET and HEAD _design/foo/_search/bar
    # EXPECTED: 404
    def test_get_invalid_search(self):
        """
        Test GET/HEAD request for missing '_design/foo/_search/bar' document ID
        """
        self.get_document_variants('_design/foo/_search/bar', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_search/bar', Expect.RESPONSE_404.value, True, path_segment_count=3)

    # GET and HEAD _design/foo/_search_info/bar
    # EXPECTED: 404
    def test_get_invalid_search_info(self):
        """
        Test GET/HEAD request for missing '_design/foo/_search_info/bar' document ID
        """
        self.get_document_variants('_design/foo/_search_info/bar', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_search_info/bar', Expect.RESPONSE_404.value, True, path_segment_count=3)

    # GET and HEAD _design/foo/_geo/bar
    # EXPECTED: 404
    def test_get_missing_geo(self):
        """
        Test GET/HEAD request for missing '_design/foo/_geo/bar' document ID
        """
        self.get_document_variants('_design/foo/_geo/bar', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_geo/bar', Expect.RESPONSE_404.value, True, path_segment_count=3)
        # with a parameter
        self.get_document_variants('_design/foo/_geo/bar?bbox=-50.52,-4.46,54.59,1.45', Expect.RESPONSE_404.value,
                                   path_segment_count=3)
        self.get_document_variants('_design/foo/_geo/bar?bbox=-50.52,-4.46,54.59,1.45', Expect.RESPONSE_404.value, True,
                                   path_segment_count=3)

    # GET and HEAD _design/foo/_geo_info/bar
    # EXPECTED: 404
    def test_get_missing_geo_info(self):
        """
        Test GET/HEAD request for missing '_design/foo/_geo_info/bar' document ID
        """
        self.get_document_variants('_design/foo/_geo_info/bar', Expect.RESPONSE_404.value, path_segment_count=3)
        self.get_document_variants('_design/foo/_geo_info/bar', Expect.RESPONSE_404.value, True, path_segment_count=3)

    # GET and HEAD _local/foo
    # EXPECTED: 200
    def test_get_local_doc(self):
        """
        Test GET/HEAD request for valid '_local/foo' document ID
        """
        self.get_document_variants('_local/foo', Expect.RESPONSE_200.value, path_segment_count=3)

    # GET and HEAD _local
    # EXPECTED: Validation exception
    def test_get_invalid_local(self):
        """
        Test GET/HEAD request for invalid '_local' document ID
        """
        self.get_document_variants('_local', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _local_docs
    # EXPECTED: Validation exception
    def test_get_invalid_local_docs(self):
        """
        Test GET/HEAD request for invalid '_local_docs' document ID
        """
        self.get_document_variants('_local_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _design_docs
    # EXPECTED: Validation exception
    def test_get_invalid_design_docs(self):
        """
        Test GET/HEAD request for invalid '_design_docs' document ID
        """
        self.get_document_variants('_design_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _changes
    # EXPECTED: Validation exception
    def test_get_invalid_changes(self):
        """
        Test GET/HEAD request for invalid '_changes' document ID
        """
        self.get_document_variants('_changes', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _ensure_full_commit
    # EXPECTED: Validation exception
    def test_get_invalid_ensure_full_commit(self):
        """
        Test GET/HEAD request for invalid '_ensure_full_commit' document ID
        """
        self.get_document_variants('_ensure_full_commit', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _index
    # EXPECTED: Validation exception
    def test_get_invalid_index(self):
        """
        Test GET/HEAD request for invalid '_index' document ID
        """
        self.get_document_variants('_index', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _revs_limit
    # EXPECTED: Validation exception
    def test_get_invalid_revs_limit(self):
        """
        Test GET/HEAD request for invalid '_revs_limit' document ID
        """
        self.get_document_variants('_revs_limit', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _security
    # EXPECTED: Validation exception
    def test_get_invalid_security(self):
        """
        Test GET/HEAD request for invalid '_security' document ID
        """
        self.get_document_variants('_security', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET and HEAD _shards
    # EXPECTED: Validation exception
    def test_get_invalid_shards(self):
        """
        Test GET/HEAD request for invalid '_shards' document ID
        """
        self.get_document_variants('_shards', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # DELETE _index/_design/foo/json/bar
    # EXPECTED: Validation exception
    def test_delete_invalid_index(self):
        """
        Test DELETE request for invalid '_index/_design/foo/json/bar' document ID
        """
        self.delete_document_variants('_index/_design/foo/json/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # DELETE _design/foo
    # EXPECTED: 200
    def test_delete_valid_ddoc(self):
        """
        Test DELETE request for valid '_design/foo' document ID
        """
        self.delete_document_variants('_design/foo', Expect.RESPONSE_200.value, path_segment_count=3)

    # DELETE _design
    # EXPECTED: Validation exception
    def test_delete_invalid_ddoc(self):
        """
        Test DELETE request for invalid '_design' document ID
        """
        # no trailing '/' on _design prefix
        self.delete_document_variants('_design', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # DELETE _local/foo
    # EXPECTED: 200
    def test_delete_valid_local_doc(self):
        """
        Test DELETE request for valid '_local/foo' document ID
        """
        self.delete_document_variants('_local/foo', Expect.RESPONSE_200.value, path_segment_count=3)

    # DELETE _local
    # EXPECTED: Validation exception
    def test_delete_invalid_local(self):
        """
        Test DELETE request for invalid '_local' document ID
        """
        # no trailing '/' on _local prefix
        self.delete_document_variants('_local', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # PUT _design/foo
    # EXPECTED: 201
    def test_put_valid_ddoc(self):
        """
        Test PUT request for valid '_design/foo' document ID
        """
        self.put_document_variants('_design/foo', Expect.RESPONSE_201.value, path_segment_count=3)

    # PUT _design
    # EXPECTED: Validation exception
    def test_put_invalid_ddoc(self):
        """
        Test PUT request for invalid '_design' document ID
        """
        self.put_document_variants('_design', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # PUT _local/foo
    # EXPECTED: 201
    def test_put_valid_local_doc(self):
        """
        Test PUT request for valid '_local/foo' document ID
        """
        self.put_document_variants('_local/foo', Expect.RESPONSE_201.value, path_segment_count=3)

    # PUT _local
    # EXPECTED: Validation exception
    def test_put_invalid_local_doc(self):
        """
        Test PUT request for invalid '_local' document ID
        """
        self.put_document_variants('_local', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # PUT _revs_limit
    # EXPECTED: Validation exception
    def test_put_invalid_revs_limit(self):
        """
        Test PUT request for invalid '_revs_limit' document ID
        """
        self.put_document_variants('_revs_limit', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # PUT _security
    # EXPECTED: Validation exception
    def test_put_invalid_security(self):
        """
        Test PUT request for invalid '_security' document ID
        """
        self.put_document_variants('_security', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET _design/foo/bar
    # EXPECTED: 200
    def test_get_valid_ddoc_attachment(self):
        """
        Test PUT request for valid '_design/foo/bar' document ID
        """
        self.get_doc_attachment_variants('_design/foo', 'bar', Expect.RESPONSE_200.value, True, path_segment_count=4)

    # PUT _design/foo/bar
    # EXPECTED: 201
    def test_put_valid_ddoc_attachment(self):
        """
        Test PUT request for valid '_design/foo/bar' document ID
        """
        self.put_doc_attachment_variants('_design/foo', 'bar', Expect.RESPONSE_201.value, True, path_segment_count=4)

    # DELETE _design/foo/bar
    # EXPECTED: 200
    def test_delete_valid_ddoc_attachment(self):
        """
        Test DELETE request for valid '_design/foo/bar' document ID
        """
        self.delete_doc_attachment_variants('_design/foo', 'bar', Expect.RESPONSE_200.value, True, path_segment_count=4)

    # GET _design/foo
    # EXPECTED: Validation exception
    def test_get_invalid_ddoc_attachment(self):
        """
        Test GET request for invalid '_design/foo' document ID
        """
        # with ddoc option enabled
        self.get_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.get_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # PUT _design/foo
    # EXPECTED: Validation exception
    def test_put_invalid_ddoc_attachment(self):
        """
        Test PUT request for invalid '_design/foo' document ID
        """
        # with ddoc option enabled
        self.put_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.put_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # DELETE _design/foo
    # EXPECTED: Validation exception
    def test_delete_invalid_ddoc_attachment(self):
        """
        Test DELETE request for invalid '_design/foo' document ID
        """
        # with ddoc option enabled
        self.delete_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.delete_doc_attachment_variants('_design', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # DELETE _index/_design/foo/json/bar
    # EXPECTED: Validation exception
    def test_delete_index_via_attachment(self):
        """
        Test DELETE requests for invalid '_index/_design/foo/json/bar'
        """
        self.delete_doc_attachment_variants('_index', '_design/foo/json/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_index', '_design/foo/json/bar',
                                            Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.delete_doc_attachment_variants('_index/_design', 'foo/json/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_index/_design', 'foo/json/bar',
                                            Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.delete_doc_attachment_variants('_index/_design/foo', 'json/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_index/_design/foo', 'json/bar',
                                            Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.delete_doc_attachment_variants('_index/_design/foo/json', 'bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_index/_design/foo/json', 'bar',
                                            Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # GET _design/foo/_view/bar
    def test_get_view_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_view/bar'
        """
        # EXPECTED: 404
        self.get_doc_attachment_variants('_design/foo/_view', 'bar', Expect.RESPONSE_404.value, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_view', 'bar', Expect.RESPONSE_404.value, True, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo', '/_view/bar', Expect.RESPONSE_404.value, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo', '/_view/bar', Expect.RESPONSE_404.value, True, path_segment_count=4)
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)
        self.get_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.get_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # PUT _design/foo/_view/bar
    def test_put_view_via_ddoc_attachment(self):
        """
        Test PUT requests for '_design/foo/_view/bar'
        """
        # EXPECTED: Validation exception
        self.put_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.put_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)
        self.put_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.put_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.put_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.put_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # DELETE _design/foo/_view/bar
    def test_delete_view_via_ddoc_attachment(self):
        """
        Test DELETE requests for '_design/foo/_view/bar'
        """
        # EXPECTED: Validation exception
        self.delete_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.delete_doc_attachment_variants('_design/foo', '_view/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)
        self.delete_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_design', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.delete_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.delete_doc_attachment_variants('_design/', 'foo/_view/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # GET _design/foo/_info
    def test_get_view_info_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_info'
        """
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_info', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_info', Expect.VALIDATION_EXCEPTION_ATT.value, True)
        self.get_doc_attachment_variants('_design', 'foo/_info', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design', 'foo/_info', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.get_doc_attachment_variants('_design/', 'foo/_info', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design/', 'foo/_info', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # GET _design/foo/_search/bar
    def test_get_search_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_search/bar'
        """
        # EXPECTED: 404
        self.get_doc_attachment_variants('_design/foo/_search', 'bar', Expect.RESPONSE_404.value, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_search', 'bar', Expect.RESPONSE_404.value, True,
                                         path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_search', 'bar?q=*.*', Expect.RESPONSE_404.value,
                                         path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_search', 'bar?q=*.*', Expect.RESPONSE_404.value, True,
                                         path_segment_count=4)
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_search/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_search/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)
        self.get_doc_attachment_variants('_design', 'foo/_search/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design', 'foo/_search/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)
        self.get_doc_attachment_variants('_design/', 'foo/_search/bar', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_design/', 'foo/_search/bar', Expect.VALIDATION_EXCEPTION_DOCID.value, True)

    # GET _design/foo/_search_info/bar
    def test_get_search_info_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_search_info/bar'
        """
        # EXPECTED: 404
        self.get_doc_attachment_variants('_design/foo/_search_info', 'bar', Expect.RESPONSE_404.value,
                                         path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_search_info', 'bar', Expect.RESPONSE_404.value, True,
                                         path_segment_count=4)
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_search_info/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_search_info/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)

    # GET _design/foo/_geo/bar
    def test_get_geo_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_geo/bar'
        """
        # EXPECTED: 404
        self.get_doc_attachment_variants('_design/foo/_geo', 'bar', Expect.RESPONSE_404.value, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_geo', 'bar', Expect.RESPONSE_404.value, True,
                                         path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_geo', 'bar?bbox=-50.52,-4.46,54.59,1.45',
                                         Expect.RESPONSE_404.value, path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_geo', 'bar?bbox=-50.52,-4.46,54.59,1.45',
                                         Expect.RESPONSE_404.value, True, path_segment_count=4)
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_geo/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_geo/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)

    # GET _design/foo/_geo_info/bar
    def test_get_geo_info_via_ddoc_attachment(self):
        """
        Test GET requests for '_design/foo/_geo_info/bar'
        """
        # EXPECTED: 404
        self.get_doc_attachment_variants('_design/foo/_geo_info', 'bar', Expect.RESPONSE_404.value,
                                         path_segment_count=4)
        self.get_doc_attachment_variants('_design/foo/_geo_info', 'bar', Expect.RESPONSE_404.value, True,
                                         path_segment_count=4)
        # EXPECTED: Validation exception
        self.get_doc_attachment_variants('_design/foo', '_geo_info/bar', Expect.VALIDATION_EXCEPTION_ATT.value)
        self.get_doc_attachment_variants('_design/foo', '_geo_info/bar', Expect.VALIDATION_EXCEPTION_ATT.value, True)

    # GET _partition/foo
    # EXPECTED: Validation exception
    def test_get_invalid_partition_info(self):
        """
        Test GET requests for '_partition/foo'
        """
        self.get_document_variants('_partition/foo', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET _partition/foo
    # EXPECTED: Validation exception
    def test_get_invalid_partition_info_via_attachment(self):
        """
        Test GET requests for '_partition/foo'
        """
        self.get_doc_attachment_variants('_partition', 'foo', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET _partition/foo/_all_docs
    # EXPECTED: Validation exception
    def test_get_partition_info(self):
        """
        Test GET requests for '_partition/foo/_all_docs'
        """
        self.get_document_variants('_partition/foo/_all_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)

    # GET _partition/foo/_all_docs
    # EXPECTED: Validation exception
    def test_get_invalid_partition_all_docs_via_attachment(self):
        """
        Test GET requests for '_partition/foo/_all_docs'
        """
        self.get_doc_attachment_variants('_partition', 'foo/_all_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)
        self.get_doc_attachment_variants('_partition/foo', '_all_docs', Expect.VALIDATION_EXCEPTION_DOCID.value)

    """UTIL FUNCTIONS"""
    def mocked_get_requests(self, rev=None, override_status_code=None):
        """
        Create a mock GET request for documents with the expected status code
        :param rev: the doc's revision (default None)
        :param override_status_code: override the status code for handling
            inner `fetch` request call within `get_attachment`
        :return: mocked Response object
        """
        resp_mock = create_autospec(requests.Response)
        if override_status_code is not None:
            resp_mock.status_code = override_status_code
        else:
            resp_mock.status_code = self.expected_enum
        if (resp_mock.status_code == 200 or resp_mock.status_code == 201
                and self.doc_id is not None):
            if rev is not None:
                resp_mock.text = f"""{{"_id": "{self.doc_id}", "_rev": "{rev}"}}"""
            else:
                resp_mock.text = f"""{{"_id": "{self.doc_id}", "_rev": "1-abc"}}"""
        elif resp_mock.status_code == 404:
            resp_mock.raise_for_status.side_effect = requests.exceptions.HTTPError
        resp_mock.encoding = None

        return resp_mock

    def mocked_get_att_requests(self):
        """
        Create a mock GET request for attachments with the expected status code
        """
        self.expected_att_content = f"""this is a text attachment"""
        # first fetch doc call with rev
        fetch_mock = self.mocked_get_requests(rev=None, override_status_code=200)
        # second get to attachment
        resp_mock = create_autospec(requests.Response)
        resp_mock.status_code = self.expected_enum
        if self.expected_enum == 200 and self.doc_id is not None and self.att_name is not None:
            resp_mock.text = self.expected_att_content
        if self.expected_enum == 404:
            resp_mock.raise_for_status.side_effect = requests.exceptions.HTTPError
        self.doc_r_session_mock.get.side_effect = [fetch_mock, resp_mock]

    def mocked_head_requests(self, override_status_code=None):
        """
        Create a mock HEAD request for documents and attachments with the expected status code
        """
        resp_mock = create_autospec(requests.Response)
        if override_status_code is not None:
            resp_mock.status_code = override_status_code
        else:
            resp_mock.status_code = self.expected_enum
        self.doc_r_session_mock.head = Mock(return_value=resp_mock)

    def mocked_delete_requests(self):
        """
        Create a mock DELETE request for documents with the expected status code
        """
        resp_mock = create_autospec(requests.Response)
        resp_mock.status_code = self.expected_enum
        if self.expected_enum == 201 and self.doc_id is not None:
            resp_mock.text = f"""{{"id": "{self.doc_id}", "rev": "2-abc", "ok": true}}"""
        self.doc_r_session_mock.delete = Mock(return_value=resp_mock)

    def mocked_delete_att_requests(self):
        """
        Create a mock DELETE request for attachments with the expected status code
        """
        # first `fetch` document call with rev
        self.doc_r_session_mock.get = Mock(return_value=self.mocked_get_requests(rev=None, override_status_code=200))
        # second delete to attachment
        resp_mock = create_autospec(requests.Response)
        resp_mock.status_code = self.expected_enum
        resp_mock.encoding = None
        if self.expected_enum == 200 and self.doc_id is not None and self.att_name is not None:
            resp_mock.text = f"""{{"id": "{self.doc_id}", "rev": "2-abc", "ok": true}}"""
        elif self.expected_enum == 404:
            resp_mock.raise_for_status.side_effect = requests.exceptions.HTTPError

        self.doc_r_session_mock.delete = Mock(return_value=resp_mock)

    def mocked_put_doc_requests(self):
        """
        Create a mock PUT request for documents with the expected status code
        """
        # mock 'doc.exists' request call within 'doc.save' function
        self.mocked_head_requests(200)
        resp_mock = create_autospec(requests.Response)
        resp_mock.status_code = self.expected_enum
        resp_mock.encoding = None
        if self.expected_enum == 201 and self.doc_id is not None:
            resp_mock.text = f"""{{"id": "{self.doc_id}", "rev": "1-abc", "ok": true}}"""
        if self.expected_enum == 404:
            resp_mock.raise_for_status.side_effect = requests.exceptions.HTTPError
        self.doc_r_session_mock.put = Mock(return_value=resp_mock)

    def mocked_put_att_requests(self):
        """
        Create a mock PUT request for attachments with the expected status code
        """
        # first `fetch` document call within `put_attachment`
        fetch_mock = self.mocked_get_requests(rev=None, override_status_code=200)
        # create Response object for PUT attachment
        resp_mock = create_autospec(requests.Response)
        resp_mock.status_code = self.expected_enum
        resp_mock.encoding = None
        if self.expected_enum == 201 and self.doc_id is not None:
            resp_mock.text = f"""{{"id": "{self.doc_id}", "rev": "2-def", "ok": true}}"""
        if self.expected_enum == 404:
            resp_mock.raise_for_status.side_effect = requests.exceptions.HTTPError
        # final fetch doc call
        second_fetch_mock = self.mocked_get_requests(rev='2-def', override_status_code=200)
        self.doc_r_session_mock.get.side_effect = [fetch_mock, second_fetch_mock]
        self.doc_r_session_mock.put = Mock(return_value=resp_mock)

    def get_document_variants(self, doc_id, expected_enum, is_ddoc=False,
                              path_segment_count=None):
        """
        Function to setup mock requests and execute GET/HEAD document requests
        """
        self.doc_id = doc_id
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_head_requests()
        self.head_document()
        self.doc_r_session_mock.get.return_value = self.mocked_get_requests()
        self.fetch_document()
        self.assert_path_segments(self.doc_r_session_mock.get.call_args_list, path_segment_count)

    def get_doc_attachment_variants(self, doc_id, att_name, expected_enum, is_ddoc=False,
                                    path_segment_count=None):
        """
        Function to setup mock requests and execute GET attachment requests
        """
        self.att_name = att_name
        self.doc_id = doc_id
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_get_att_requests()
        self.get_doc_attachment()
        self.assert_path_segments(self.doc_r_session_mock.get.call_args_list, path_segment_count)

    def put_document_variants(self, doc_id, expected_enum, is_ddoc=False,
                              path_segment_count=None):
        """
        Function to setup mock requests and execute PUT document requests
        """
        self.doc_id = doc_id
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_put_doc_requests()
        self.put_document()
        self.assert_path_segments(self.doc_r_session_mock.put.call_args_list, path_segment_count)

    def put_doc_attachment_variants(self, doc_id, att_name, expected_enum, is_ddoc=False,
                                    path_segment_count=None):
        """
        Function to setup mock requests and execute PUT attachment requests
        """
        self.att_name = att_name
        self.doc_id = doc_id
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_put_att_requests()
        self.put_doc_attachment()
        self.assert_path_segments(self.doc_r_session_mock.put.call_args_list, path_segment_count)

    def delete_document_variants(self, doc_id, expected_enum, is_ddoc=False,
                                 path_segment_count=None):
        """
        Function to setup mock requests and execute DELETE document requests
        """
        self.doc_id = doc_id
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_delete_requests()
        self.delete_document()
        self.assert_path_segments(self.doc_r_session_mock.delete.call_args_list, path_segment_count)

    def delete_doc_attachment_variants(self, doc_id, attname, expected_enum, is_ddoc=False,
                                       path_segment_count=None):
        """
        Function to setup mock requests and execute DELETE attachment requests
        """
        self.doc_id = doc_id
        self.att_name = attname
        self.expected_enum = expected_enum
        self.is_ddoc = is_ddoc
        self.mocked_delete_att_requests()
        self.delete_doc_attachment()
        self.assert_path_segments(self.doc_r_session_mock.delete.call_args_list, path_segment_count)

    """HTTP REQUEST FUNCTIONS"""
    def head_document(self):
        try:
            resp = self.create_doc(self.doc_id, self.is_ddoc).exists()
            if self.expected_enum == 200 or self.expected_enum == 201:
                self.assertTrue(resp)
            elif self.expected_enum == 404:
                self.assertFalse(resp)
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)

    def delete_document(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            doc['_rev'] = '1-abc'
            doc.delete()
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, doc['_id'])
            self.assertFalse('rev' in doc)
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    def fetch_document(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            doc.fetch()
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, doc['_id'])
            self.assertIsNotNone(doc['_rev'])
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    def put_document(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            doc.save()
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, doc['_id'])
            self.assertIsNotNone(doc['_rev'])
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    def delete_doc_attachment(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            doc['_rev'] = '1-abc'
            resp = doc.delete_attachment(self.att_name)
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, doc['_id'])
            self.assertEqual(self.doc_id, resp['id'])
            self.assertEqual(doc['_rev'], resp['rev'])
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    def get_doc_attachment(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            resp_att = doc.get_attachment(self.att_name, attachment_type='text')
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, doc['_id'])
            self.assertIsNotNone(resp_att)
            self.assertEqual(resp_att, self.expected_att_content)
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    def put_doc_attachment(self):
        try:
            doc = self.create_doc(self.doc_id, self.is_ddoc)
            resp_att = doc.put_attachment(self.att_name, content_type='utf-8', data='test')
            self.assertIsNotNone(resp_att)
            self.assertTrue(isinstance(self.expected_enum, int),
                            f"""Expected value {self.expected_enum} is not an int status code.""")
            self.assertTrue(self.expected_enum < 400,
                            f"""Expected value {self.expected_enum} is not a successful status code.""")
            self.assertEqual(self.doc_id, resp_att['id'])
            self.assertEqual(resp_att['id'], doc['_id'])
            self.assertEqual(doc['_rev'], resp_att['rev'])
            self.assertEqual(resp_att['ok'], True)
        except CloudantArgumentError as cae:
            self.assert_exception_msg(cae)
        except requests.exceptions.HTTPError as err:
            self.assertTrue(id(self.expected_enum), id(err))

    """HELPER FUNCTIONS"""
    def create_doc(self, doc_id=None, is_ddoc=False):
        """
        Function to create and return a Document or DesignDocument object.
        """
        if is_ddoc:
            if doc_id is not None:
                doc = DesignDocument(self.db, doc_id)
            else:
                doc = DesignDocument(self.db)
        elif doc_id is not None:
            doc = Document(self.db, doc_id)
        else:
            doc = Document(self.db)
        self.assertIsNone(doc.get('_rev'))
        return doc

    def assert_exception_msg(self, cae):
        """
        Function to assert whether the exception message is for an invalid
        document ID or an attachment name.
        """
        self.assertTrue(id(self.expected_enum), id(cae))
        # Check that actual exception message starts with the expected msg
        if str(cae).startswith(str(self.expected_enum)):
            # Figure out which exception msg to assert against
            if str(cae).startswith(ValidationExceptionMsg.ATTACHMENT.value):
                self.assertEqual(str(cae), f"""{ValidationExceptionMsg.ATTACHMENT.value} {self.att_name}""")
            elif str(cae).startswith(ValidationExceptionMsg.DOC.value):
                self.assertEqual(str(cae), f"""{ValidationExceptionMsg.DOC.value} {self.doc_id}""")
        else:
            self.fail('Expected CloudantArgumentError message should equal actual error message.')

    def assert_path_segments(self, actual_call_args_list, exp_segment_count):
        """
        Function to assert the number of path segments from a mock request
        """
        # If there's no segment count, verify that the test case expects an argument error
        if exp_segment_count is None:
            self.assertTrue(isinstance(self.expected_enum, CloudantArgumentError), 'Path segment count should exist '
                                                                                   'when testing against valid '
                                                                                   'document or attachment names.')
        else:
            # get latest call in list
            url, headers = actual_call_args_list[len(actual_call_args_list) - 1]
            # there should only be one mocked url
            self.assertEqual(len(url), 1)
            # parse path of url and remove first / path segment
            path = urlparse(url[0]).path[1:]
            actual_segment_count = len(path.split('/'))
            self.assertEqual(actual_segment_count, exp_segment_count)
