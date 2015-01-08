CIRRUS_UPDATE_SENTINEL

Release: 0.0.1 Created: 2015-01-08T20:56:11.861427
 - Commit History:
 -- Author: petevg
 --- 2015-01-08T20:55:49Z: Updated cirrus.conf w/ pypi attirbutes.
 --- 2015-01-08T14:53:14Z: Improved docstring for replication_state.
 --- 2015-01-08T14:51:17Z: Merge pull request #9 from evansde77/feature/replicator_db_object

Feature/replicator db object
 --- 2015-01-07T21:34:34Z: Got rid of stray print statement.
 --- 2015-01-07T19:00:15Z: Added test_replication_state. This seemed to push the number of tests over a threshold, and I'm consistently seeing replication docs hang out and not get updated -- I'm pushing so that others can take a look.
 --- 2015-01-07T13:43:07Z: Added a Replicator object, which is basically a wrapper around a Database object.

Added some methods to account and database to faciliate automagic in piecing together the replication.

Added 'creds' property to Database objects, and used it in replications.

Added a .delete method to Document, which supports a .stop_replication method to the Replicator object.
 --- 2014-12-23T14:40:35Z: Merge pull request #6 from evansde77/feature/changes_feed

Speaking of changes feeds ... I made one.
 --- 2014-12-18T21:58:47Z: Speaking of changes feeds ... I made one.
 --- 2014-12-17T14:27:42Z: Merge pull request #5 from evansde77/feature/bulk_docs_apis

Feature/bulk docs apis
 --- 2014-12-16T14:59:26Z: Updated docstring on database.__iter__ for clarity.
 --- 2014-12-16T14:44:34Z: Added __iter__ method to database.py that will fetch docs incrementally, and iterate through them.
 --- 2014-12-11T22:18:29Z: Added emacs temp files to .gitignore.
 --- 2014-12-10T19:48:56Z: Merge pull request #4 from evansde77/bug/fix_tests

Added 'test' to the names of the test filenames.
 --- 2014-12-09T15:05:26Z: Added venv to ignore.
 --- 2014-12-09T14:59:54Z: Added 'test' to the names of the test filenames.

nosetests will not find them if 'test' not in name.
 -- Author: evansde77
 --- 2014-11-12T16:45:55Z: changes, start on tests
 --- 2014-10-31T16:20:12Z: add credential helper
 --- 2014-10-31T16:17:20Z: add reqs
 --- 2014-10-31T16:17:00Z: setup cirrus
 --- 2014-10-31T16:11:30Z: add basic test workout
 --- 2014-10-31T14:58:30Z: initial proto
 --- 2014-07-09T16:53:14Z: Initial commit

Release: 0.0.1 Created: 2015-01-08T20:40:39.467982
 - Commit History:
 -- Author: petevg
 --- 2015-01-08T14:53:14Z: Improved docstring for replication_state.
 --- 2015-01-08T14:51:17Z: Merge pull request #9 from evansde77/feature/replicator_db_object

Feature/replicator db object
 --- 2015-01-07T21:34:34Z: Got rid of stray print statement.
 --- 2015-01-07T19:00:15Z: Added test_replication_state. This seemed to push the number of tests over a threshold, and I'm consistently seeing replication docs hang out and not get updated -- I'm pushing so that others can take a look.
 --- 2015-01-07T13:43:07Z: Added a Replicator object, which is basically a wrapper around a Database object.

Added some methods to account and database to faciliate automagic in piecing together the replication.

Added 'creds' property to Database objects, and used it in replications.

Added a .delete method to Document, which supports a .stop_replication method to the Replicator object.
 --- 2014-12-23T14:40:35Z: Merge pull request #6 from evansde77/feature/changes_feed

Speaking of changes feeds ... I made one.
 --- 2014-12-18T21:58:47Z: Speaking of changes feeds ... I made one.
 --- 2014-12-17T14:27:42Z: Merge pull request #5 from evansde77/feature/bulk_docs_apis

Feature/bulk docs apis
 --- 2014-12-16T14:59:26Z: Updated docstring on database.__iter__ for clarity.
 --- 2014-12-16T14:44:34Z: Added __iter__ method to database.py that will fetch docs incrementally, and iterate through them.
 --- 2014-12-11T22:18:29Z: Added emacs temp files to .gitignore.
 --- 2014-12-10T19:48:56Z: Merge pull request #4 from evansde77/bug/fix_tests

Added 'test' to the names of the test filenames.
 --- 2014-12-09T15:05:26Z: Added venv to ignore.
 --- 2014-12-09T14:59:54Z: Added 'test' to the names of the test filenames.

nosetests will not find them if 'test' not in name.
 -- Author: evansde77
 --- 2014-11-12T16:45:55Z: changes, start on tests
 --- 2014-10-31T16:20:12Z: add credential helper
 --- 2014-10-31T16:17:20Z: add reqs
 --- 2014-10-31T16:17:00Z: setup cirrus
 --- 2014-10-31T16:11:30Z: add basic test workout
 --- 2014-10-31T14:58:30Z: initial proto
 --- 2014-07-09T16:53:14Z: Initial commit
