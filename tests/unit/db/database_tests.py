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
_database_tests_

database module - Unit tests for CouchDatabase and CloudantDatabase classes

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import requests
import posixpath
import os

from cloudant.database import CouchDatabase, CloudantDatabase
from cloudant.result import Result
from cloudant.errors import CloudantException
from cloudant.document import Document
from cloudant.design_document import DesignDocument

from unit_t_db_base import UnitTestDbBase

class DatabaseTests(UnitTestDbBase):
    """
    CouchDatabase/CloudantDatabase unit tests
    """

    def setUp(self):
        """
        Set up test attributes for CouchDB Database tests
        """
        super(DatabaseTests, self).setUp()
        self.client.connect()
        self.test_dbname = self.dbname()
        self.db = self.client._DATABASE_CLASS(self.client, self.test_dbname)
        self.db.create()

    def tearDown(self):
        """
        Ensure the client is new for each test
        """
        self.db.delete()
        self.client.disconnect()
        del self.test_dbname
        del self.db
        super(DatabaseTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a database
        """
        self.assertEqual(self.db.cloudant_account, self.client)
        self.assertEqual(self.db.database_name, self.test_dbname)
        self.assertEqual(self.db.r_session, self.client.r_session)
        self.assertIsInstance(self.db.result, Result)

    def test_retrieve_db_url(self):
        """
        Test retrieving the database URL
        """
        self.assertEqual(
            self.db.database_url,
            posixpath.join(self.client.cloudant_url, self.test_dbname)
            )

    def test_retrieve_creds(self):
        """
        Test retrieving account credentials
        """
        expected_keys = ['basic_auth', 'user_ctx']
        self.assertTrue(all(x in expected_keys for x in self.db.creds.keys()))
        self.assertTrue(self.db.creds['basic_auth'].startswith('Basic'))
        self.assertEqual(self.db.creds['user_ctx']['name'], self.user)

    def test_exists(self):
        """
        Test database exists fucntionality
        """
        self.assertTrue(self.db.exists())
        # Construct a database object that does not exist remotely
        fake_db = self.client._DATABASE_CLASS(self.client, 'no-such-db')
        self.assertFalse(fake_db.exists())

    def test_create_db_delete_db(self):
        """
        Test creating and deleting a database
        """
        dbname = self.dbname()
        db = self.client._DATABASE_CLASS(self.client, dbname)
        try:
            db.create()
            self.assertTrue(db.exists())
            # No issue should arise if attempting to create existing database
            db_2 = db.create()
            self.assertEqual(db, db_2)
        except Exception, err:
            self.fail('Exception {0} was raised.'.format(str(err)))
        finally:
            db.delete()
            self.assertFalse(db.exists())

    def test_delete_exception(self):
        """
        Test deleting a database that does not exist
        """
        try:
            fake_db = self.client._DATABASE_CLASS(self.client, 'no-such-db')
            fake_db.delete()
            self.fail('Above statement should raise an Exception')
        except requests.HTTPError, err:
            self.assertEqual(err.response.status_code, 404)

    def test_retrieve_db_metadata(self):
        """
        Test retrieving the database metadata information
        """
        resp = self.db.r_session.get(
            posixpath.join(self.client.cloudant_url, self.test_dbname)
            )
        expected = resp.json()
        actual = self.db.metadata()
        # The update_seq will likely be different each time you get the
        # metadata from Cloudant.  Just check that it exists and then 
        # compare the remainder of the actual and expected metadata.
        self.assertIsNotNone(actual.get('update_seq'))
        del expected['update_seq']
        del actual['update_seq']
        self.assertEqual(actual, expected)

    def test_retrieve_document_count(self):
        """
        Test retrieving the number of documents currently in the database
        """
        self.populate_db_with_documents(6)
        self.assertEqual(self.db.doc_count(), 6)

    def test_create_document_with_id(self):
        """
        Test creating a document using a supplied document id
        """
        data = {'_id': 'julia06', 'name': 'julia', 'age': 6}
        doc = self.db.create_document(data)
        self.assertEqual(self.db['julia06'], doc)
        self.assertEqual(doc['_id'], data['_id'])
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['name'], data['name'])
        self.assertEqual(doc['age'], data['age'])
        try:
            self.db.create_document(data, throw_on_exists=True)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException, err:
            self.assertEqual(
                str(err),
                'Error - Document with id julia06 already exists.'
                )

    def test_create_document_without_id(self):
        """
        Test creating a document without supplying a document id
        """
        data = {'name': 'julia', 'age': 6}
        doc = self.db.create_document(data)
        self.assertEqual(self.db[doc['_id']], doc)
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['name'], data['name'])
        self.assertEqual(doc['age'], data['age'])

    def test_create_empty_document(self):
        """
        Test creating an empty document
        """
        empty_doc = self.db.new_document()
        self.assertEqual(self.db[empty_doc['_id']], empty_doc)
        self.assertTrue(all(x in ['_id', '_rev'] for x in empty_doc.keys()))
        self.assertTrue(empty_doc['_rev'].startswith('1-'))

    def test_retrieve_design_documents(self):
        """
        Test retrieving all design documents
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        ddoc1 = self.db.create_document(data)
        data = {'_id': '_design/ddoc02','views': {'view02': {"map": map_func}}}
        ddoc2 = self.db.create_document(data)
        raw_ddocs = self.db.design_documents()
        self.assertEqual(len(raw_ddocs), 2)
        self.assertTrue(
            all(x in [raw_ddocs[0]['key'], raw_ddocs[1]['key']]
                for x in self.db.keys()
                )
            )
        self.assertTrue(
            all(x in [raw_ddocs[0]['id'], raw_ddocs[1]['id']]
                for x in self.db.keys()
                )
            )
        self.assertTrue(
            all(x in [raw_ddocs[0]['doc'], raw_ddocs[1]['doc']]
                for x in [ddoc1, ddoc2]
                )
            )

    def test_retrieve_design_document_list(self):
        """
        Test retrieving a list of design document names
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        data = {'_id': '_design/ddoc02','views': {'view02': {"map": map_func}}}
        self.db.create_document(data)
        ddoc_list = self.db.list_design_documents()
        self.assertTrue(all(x in ddoc_list for x in self.db.keys()))

    def test_retrieve_design_document(self):
        """
        Test retrieve a specific design document
        """
        # Get an empty design document object that does not exist remotely
        local_ddoc = self.db.get_design_document('_design/ddoc01')
        self.assertEqual(local_ddoc, {'views': {}})

        # Add the design document to the database
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        local_ddoc.add_view('view01', map_func)
        local_ddoc.save()

        # Get the recently created design document that now exists remotely
        ddoc = self.db.get_design_document('_design/ddoc01')
        self.assertEqual(ddoc, local_ddoc)

    def test_retrieve_view_results(self):
        """
        Test retrieving Result wrapped output from a design document view
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        self.populate_db_with_documents()

        # Test with default Result
        rslt = self.db.get_view_result('_design/ddoc01', 'view01')
        self.assertIsInstance(rslt, Result)
        self.assertEqual(rslt[:1], rslt['julia000'])

        #Test with custom Result
        rslt = self.db.get_view_result(
            '_design/ddoc01',
            'view01',
            descending=True,
            reduce=False)
        self.assertIsInstance(rslt, Result)
        self.assertEqual(rslt[:1], rslt['julia099'])

    def test_retrieve_raw_view_results(self):
        """
        Test retrieving raw output from a design document view
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        self.populate_db_with_documents()

        raw_rslt = self.db.get_view_raw_result('_design/ddoc01', 'view01')
        self.assertIsInstance(raw_rslt, dict)
        self.assertEqual(len(raw_rslt.get('rows')), 100)

    def test_all_docs(self):
        """
        Test the all_docs functionality
        """
        self.populate_db_with_documents()
        data = self.db.all_docs(
            limit=3,
            keys=['julia006', 'julia024', 'julia045', 'julia099']
        )
        self.assertEqual(len(data.get('rows')), 3)
        self.assertEqual(data['rows'][0]['key'], 'julia006')
        self.assertEqual(data['rows'][1]['key'], 'julia024')
        self.assertEqual(data['rows'][2]['key'], 'julia045')

    def test_custom_result_context_manager(self):
        """
        Test using the database custom result context manager
        """
        self.populate_db_with_documents()
        with self.db.custom_result(startkey='julia010', endkey='julia012') as rslt:
            self.assertIsInstance(rslt, Result)
            keys_returned = [i['key'] for i in rslt]
            expected_keys = ['julia010', 'julia011', 'julia012']
            self.assertTrue(all(x in keys_returned for x in expected_keys))

    def test_keys(self):
        """
        Test retrieving the document keys from the database
        """
        self.assertEqual(self.db.keys(), [])
        self.populate_db_with_documents(3)
        self.assertEqual(
            self.db.keys(remote=True),
            ['julia000', 'julia001', 'julia002']
            )

    def test_get_non_existing_doc_via_getitem(self):
        """
        Test __getitem__ when retrieving a non-existing document
        """
        try:
            doc = self.db['no_such_doc']
            self.fail('Above statement should raise a KeyError')
        except KeyError:
            pass

    def test_get_db_via_getitem(self):
        """
        Test __getitem__ when retrieving a document
        """

        # Add a design document
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        expected_ddoc = self.db.get_design_document('_design/ddoc01')
        expected_ddoc.add_view('view01', map_func)
        expected_ddoc.save()

        # Add three standard documents
        self.populate_db_with_documents(3)

        # Test __get_item__ for standard document
        doc = self.db['julia001']
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.get('_id'), 'julia001')
        self.assertTrue(doc.get('_rev').startswith('1-'))
        self.assertEqual(doc.get('name'), 'julia')
        self.assertEqual(doc.get('age'), 1)

        # Test __get_item__ for design document
        ddoc = self.db['_design/ddoc01']
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertTrue(ddoc, expected_ddoc)

    def test_document_iteration_under_fetch_limit(self):
        """
        Test __iter__ works as expected when the number of documents in
        the database is less than the database fetch limit
        """
        docs = []

        # Check iterating when no documents exist
        for doc in self.db:
            self.fail('There should be no documents in the database yet!!')
        # Check that iteration yields appropriate contents
        self.populate_db_with_documents(3)
        age = 0
        for doc in self.db:
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], age)
            docs.append(doc)
            age += 1
        self.assertEqual(len(docs), 3)
        # Check that the local database object has been populated
        # with the appropriate documents
        expected_keys = ['julia{0:03d}'.format(i) for i in xrange(3)]
        self.assertTrue(all(x in self.db.keys()for x in expected_keys))
        for id in self.db.keys():
            doc = self.db.get(id)
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], id)
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], int(id[len(id) - 3 : len(id)]))

    def test_document_iteration_over_fetch_limit(self):
        """
        Test __iter__ works as expected when the number of documents in
        the database is more than the database fetch limit
        """
        docs = []
        # Check iterating when no documents exist
        for doc in self.db:
            self.fail('There should be no documents in the database yet!!')
        # Check that iteration yields appropriate contents
        self.populate_db_with_documents(103)
        age = 0
        for doc in self.db:
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], age)
            docs.append(doc)
            age += 1
        self.assertEqual(len(docs), 103)
        # Check that the local database object has been populated
        # with the appropriate documents
        expected_keys = ['julia{0:03d}'.format(i) for i in xrange(103)]
        self.assertTrue(all(x in self.db.keys()for x in expected_keys))
        for id in self.db.keys():
            doc = self.db.get(id)
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], id)
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], int(id[len(id) - 3 : len(id)]))

    def test_bulk_docs_creation(self):
        docs = [
            {'_id': 'julia{0:03d}'.format(i), 'name': 'julia', 'age': i}
            for i in xrange(3)
        ]
        results = self.db.bulk_docs(docs)
        self.assertEqual(len(results), 3)
        i = 0
        for result in results:
            self.assertEqual(result['id'], 'julia{0:03d}'.format(i))
            self.assertTrue(result['rev'].startswith('1-'))
            i += 1

    def test_bulk_docs_update(self):
        self.populate_db_with_documents(3)
        docs = []
        for doc in self.db:
            doc['name'] = 'jules'
            docs.append(doc)
        results = self.db.bulk_docs(docs)
        self.assertEqual(len(results), 3)
        i = 0
        for result in results:
            self.assertEqual(result['id'], 'julia{0:03d}'.format(i))
            self.assertTrue(result['rev'].startswith('2-'))
            i += 1
        age = 0
        for doc in self.db:
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('2-'))
            self.assertEqual(doc['name'], 'jules')
            self.assertEqual(doc['age'], age)
            age += 1
        self.assertEqual(age, 3)

@unittest.skipUnless(
     os.environ.get('RUN_CLOUDANT_TESTS') is not None,
     'Skipping Cloudant specific Database tests'
     )
class CloudantDatabaseTests(UnitTestDbBase):
    """
    Cloudant specific Database unit tests
    """

    # Add Cloudant specific tests
    pass


if __name__ == '__main__':
    unittest.main()
