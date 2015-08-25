"""
database unittests
"""

import mock
import unittest

from cloudant.database import CouchDatabase


class CouchDBTest(unittest.TestCase):
    def setUp(self):
        self.mock_session = mock.Mock()
        self.mock_session.get = mock.Mock()
        self.mock_session.post = mock.Mock()
        self.mock_session.put = mock.Mock()
        self.mock_session.delete = mock.Mock()

        self.account = mock.Mock()
        self.account._cloudant_url = "https://bob.cloudant.com"
        self.account._r_session = self.mock_session

        self.username = "bob"
        self.db_name = "testdb"
        self.c = CouchDatabase(self.account, self.db_name)

        self.db_info = {
            "update_seq": "1-g1AAAADfeJzLYWBg",
            "db_name": self.db_name,
            "sizes": {
                "file": 1528585,
                "external": 5643,
                "active": None
            },
            "purge_seq": 0,
            "other": {
                "data_size": 5643
            },
            "doc_del_count": 2,
            "doc_count": 13,
            "disk_size": 1528585,
            "disk_format_version": 6,
            "compact_running": False,
            "instance_start_time": "0"
        }

        self.ddocs = {
            "rows": [
                {
                    "id": "_design/test",
                    "key": "_design/test",
                    "value": {
                        "rev": "1-4e6d6671b0ba9ba994a0f5e7e8de1d9d"
                    },
                    "doc": {
                        "_id": "_design/test",
                        "_rev": "1-4e6d6671b0ba9ba994a0f5e7e8de1d9d",
                        "views": {
                            "test": {
                                "map": "function (doc) {emit(doc._id, 1);}"
                            }
                        }
                    }
                }
            ]
        }

        self.all_docs = {
            "total_rows": 13,
            "offset": 0,
            "rows": [
                {
                    "id": "snipe",
                    "key": "snipe",
                    "value": {
                        "rev": "1-4b2fb3b7d6a226b13951612d6ca15a6b"
                    }
                },
                {
                    "id": "zebra",
                    "key": "zebra",
                    "value": {
                        "rev": "1-750dac460a6cc41e6999f8943b8e603e"
                    }
                }
            ]
        }

    def test_create(self):
        mock_resp = mock.Mock()
        mock_resp.status_code = 201
        self.mock_session.put = mock.Mock()
        self.mock_session.put.return_value = mock_resp

        self.c.create()

        self.failUnless(self.mock_session.put.called)

    def test_delete(self):
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        self.mock_session.delete = mock.Mock()
        self.mock_session.delete.return_value = mock_resp

        self.c.delete()

        self.failUnless(self.mock_session.delete.called)

    def test_db_info(self):
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json = mock.Mock(return_value=self.db_info)
        self.mock_session.get = mock.Mock(return_value=mock_resp)

        exists_resp = self.c.exists()
        meta_resp = self.c.metadata()
        count_resp = self.c.doc_count()

        self.failUnless(self.mock_session.get.called)
        self.assertEqual(self.mock_session.get.call_count, 3)
        self.assertEqual(exists_resp, True)
        self.assertEqual(meta_resp, self.db_info)
        self.assertEqual(count_resp, self.db_info["doc_count"])

    def test_ddocs(self):
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock(return_value=False)
        mock_resp.json = mock.Mock(return_value=self.ddocs)
        self.mock_session.get = mock.Mock(return_value=mock_resp)

        ddocs = self.c.design_documents()
        ddoc_list = self.c.list_design_documents()

        self.failUnless(self.mock_session.get.called)
        self.assertEqual(self.mock_session.get.call_count, 2)
        self.assertEqual(ddocs[0]["id"], "_design/test")
        self.assertEqual(ddoc_list[0], "_design/test")

    def test_all_docs(self):
        mock_resp = mock.Mock()
        mock_resp.json = mock.Mock(return_value=self.all_docs)
        self.mock_session.get = mock.Mock(return_value=mock_resp)

        all_docs = self.c.all_docs()
        keys = self.c.keys(remote=True)

        self.failUnless(self.mock_session.get.called)
        self.assertDictContainsSubset({"id": "snipe"}, all_docs["rows"][0])
        self.assertDictContainsSubset({"id": "zebra"}, all_docs["rows"][1])
        self.assertListEqual(keys, ["snipe", "zebra"])

if __name__ == '__main__':
    unittest.main()
