"""
Replicator Test
"""

import logging
import posixpath
import sys
import time
import uuid
import unittest

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant
from cloudant.replicator import ReplicatorDatabase

def setup_logging():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    log.addHandler(handler)
    return log

LOG = setup_logging()

class ReplicatorTest(unittest.TestCase):
    """
    Excercise our replicator class to ensure that it does its thing.
    """

    def setUp(self):
        self.user, self.passwd = read_dot_cloudant(filename="~/.clou")
        self.replication_ids = []
        self.dbs = []

    def tearDown(self):
        with cloudant(self.user, self.passwd) as c:
            replicator_db = ReplicatorDatabase(c)

            while self.replication_ids:
                replicator_db.stop_replication(self.replication_ids.pop())

            while self.dbs:
                c.delete_database(self.dbs.pop())


    def test_init(self):
        """
        _test_init_

        Verify that we can init our database object.

        """
        with cloudant(self.user, self.passwd) as c:
            replicator = ReplicatorDatabase(c)
            replicator.all_docs()

    def test_create_replication(self):
        """
        _test_create_replication_

        Make a couple of test databases, and confirm that docs from
        one get transferred to t'other.

        """
        dbsource = u"test_create_replication_source_{}".format(
            unicode(uuid.uuid4()))
        dbtarget = u"test_create_replication_target_{}".format(
            unicode(uuid.uuid4()))

        self.dbs = [dbsource, dbtarget]

        with cloudant(self.user, self.passwd) as c:
            dbs = c.create_database(dbsource)
            dbt = c.create_database(dbtarget)

            doc1 = dbs.create_document(
                {"_id": "doc1", "testing": "document 1"}
            )
            doc2 = dbs.create_document(
                {"_id": "doc2", "testing": "document 1"}
            )
            doc3 = dbs.create_document(
                {"_id": "doc3", "testing": "document 1"}
            )

            replicator = ReplicatorDatabase(c)
            repl_id = u"test_create_replication_{}".format(
                unicode(uuid.uuid4()))
            self.replication_ids.append(repl_id)

            ret = replicator.create_replication(
                source_db=dbs,
                target_db=dbt,
                repl_id=repl_id,
                continuous=False,
            )

            try:
                repl_doc = replicator[repl_id]
            except KeyError:
                repl_doc = None
            if not repl_doc or not (repl_doc.get(
                    '_replication_state', "none") in ('completed, error')):
                for change in replicator.changes():
                    if change.get('id') == repl_id:
                        try:
                            repl_doc = replicator[repl_id]
                            repl_doc.fetch()
                        except KeyError:
                            pass
                        if repl_doc and (repl_doc.get(
                                '_replication_state',
                                "none") in ('completed', 'error')):
                            break
                        else:
                            LOG.debug(
                                u"Waiting for replication to complete "
                                u"(repl_doc: {})".format(repl_doc)
                            )

            self.assertTrue(repl_doc)
            self.assertEqual(repl_doc.get('_replication_state'), 'completed')
            for d in ['doc1', 'doc2', 'doc3']:
                self.assertTrue(dbt[d])
                self.assertEqual(dbt[d]['testing'], dbs[d]['testing'])

    def test_follow_replication(self):
        """
        _test_follow_replication_

        Test to make sure that we can follow a replication.

        """
        dbsource = u"test_follow_replication_source_{}".format(
            unicode(uuid.uuid4()))
        dbtarget = u"test_follow_replication_target_{}".format(
            unicode(uuid.uuid4()))

        self.dbs = [dbsource, dbtarget]

        with cloudant(self.user, self.passwd) as c:
            dbs = c.create_database(dbsource)
            dbt = c.create_database(dbtarget)

            doc1 = dbs.create_document(
                {"_id": "doc1", "testing": "document 1"}
            )
            doc2 = dbs.create_document(
                {"_id": "doc2", "testing": "document 1"}
            )
            doc3 = dbs.create_document(
                {"_id": "doc3", "testing": "document 1"}
            )

            replicator = ReplicatorDatabase(c)
            repl_id = u"test_follow_replication_{}".format(
                unicode(uuid.uuid4()))
            self.replication_ids.append(repl_id)

            ret = replicator.create_replication(
                source_db=dbs,
                target_db=dbt,
                repl_id=repl_id,
                continuous=False,
            )
            updates = [
                update for update in replicator.follow_replication(repl_id)
            ]
            self.assertTrue(len(updates) > 0)
            self.assertEqual(updates[-1]['_replication_state'], 'completed')

    @unittest.skip("Doesn't reliably get into error state on couch side.")
    def test_follow_replication_with_errors(self):
        """
        _test_follow_replication_with_errors_

        Test to make sure that we exit the follow loop when we submit
        a bad replication.

        """
        dbsource = u"test_follow_replication_source_error_{}".format(
            unicode(uuid.uuid4()))
        dbtarget = u"test_follow_replication_target_error_{}".format(
            unicode(uuid.uuid4()))

        self.dbs = [dbsource, dbtarget]

        with cloudant(self.user, self.passwd) as c:
            dbs = c.create_database(dbsource)
            dbt = c.create_database(dbtarget)

            doc1 = dbs.create_document(
                {"_id": "doc1", "testing": "document 1"}
            )
            doc2 = dbs.create_document(
                {"_id": "doc2", "testing": "document 1"}
            )
            doc3 = dbs.create_document(
                {"_id": "doc3", "testing": "document 1"}
            )

            replicator = ReplicatorDatabase(c)
            repl_id = u"test_follow_replication_{}".format(
                unicode(uuid.uuid4()))
            self.replication_ids.append(repl_id)

            ret = replicator.create_replication(
                source_db=dbs,
                target_db=dbt,
                # Deliberately override these good params with bad params
                source=dbsource + "foo",
                target=dbtarget + "foo",
                repl_id=repl_id,
                continuous=False,
            )
            updates = [
                update for update in replicator.follow_replication(repl_id)
            ]
            self.assertTrue(len(updates) > 0)
            self.assertEqual(updates[-1]['_replication_state'], 'error')


    def test_replication_state(self):
        """
        _test_replication_state_

        Verify that we can get the replication state.

        """
        dbsource = u"test_replication_state_source_{}".format(
            unicode(uuid.uuid4()))
        dbtarget = u"test_replication_state_target_{}".format(
            unicode(uuid.uuid4()))

        self.dbs = [dbsource, dbtarget]

        with cloudant(self.user, self.passwd) as c:
            dbs = c.create_database(dbsource)
            dbt = c.create_database(dbtarget)

            doc1 = dbs.create_document(
                {"_id": "doc1", "testing": "document 1"}
            )
            doc2 = dbs.create_document(
                {"_id": "doc2", "testing": "document 1"}
            )
            doc3 = dbs.create_document(
                {"_id": "doc3", "testing": "document 1"}
            )

            replicator = ReplicatorDatabase(c)
            repl_id = u"test_replication_state_{}".format(
                unicode(uuid.uuid4()))
            self.replication_ids.append(repl_id)

            ret = replicator.create_replication(
                source_db=dbs,
                target_db=dbt,
                repl_id=repl_id,
                continuous=False,
            )
            replication_state = "not_yet_set"
            while True:
                # Verify that replication_state returns either None
                # (if the field doesn't exist yet), or a valid
                # replication state.
                replication_state = replicator.replication_state(repl_id)
                if replication_state is not None:
                    self.assertTrue(
                        replication_state in [
                            'completed',
                            'error',
                            'triggered'
                        ]
                    )
                    if replication_state in ('error', 'completed'):
                        break
                LOG.debug("got replication state: {}".format(
                    replication_state))
                time.sleep(1)

    def test_list_replications(self):
        """
        _test_list_replications_

        Verify that we get a list of replications documents back when
        we got to list replications.

        """

        with cloudant(self.user, self.passwd) as c:
            replicator = ReplicatorDatabase(c)
            repl_ids = []
            num_reps = 3

            for i in range(0, num_reps):
                tag = "{0}_{1}".format(i, unicode(uuid.uuid4()))
                dbsource = u"test_list_repl_src_{}".format(tag)
                dbtarget = u"test_list_repl_tgt_{}".format(tag)

                self.dbs.append(dbsource)
                self.dbs.append(dbtarget)

                dbs = c.create_database(dbsource)
                dbt = c.create_database(dbtarget)

                doc1 = dbs.create_document(
                    {"_id": "doc1", "testing": "document 1"}
                )

                repl_id = u"test_create_replication_{}".format(tag)
                self.replication_ids.append(repl_id)
                repl_ids.append(repl_id)

                ret = replicator.create_replication(
                    source_db=dbs,
                    target_db=dbt,
                    repl_id=repl_id,
                    continuous=False
                )

            replications = replicator.list_replications()
            ids = [doc['_id'] for doc in replications]

            found_ids = [i for i in ids if i in repl_ids]

            self.assertEqual(num_reps, len(found_ids))
