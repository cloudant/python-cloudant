2.0.1 (Unreleased)
==================
- [FIX] Fixed issue with Windows platform compatibility,replaced usage of os.uname for the user-agent string.

2.0.0 (2016-05-02)
==================
- [BREAKING] Renamed modules account.py, errors.py, indexes.py, views.py, to client.py, error.py, index.py, and view.py.
- [BREAKING] Removed the ``make_result`` method from ``View`` and ``Query`` classes.  If you need to make a query or view result, use ``CloudantDatabase.get_query_result``, ``CouchDatabase.get_view_result``, or the ``View.custom_result`` context manager.  Additionally, the ``Result`` and ``QueryResult`` classes can be called directly to construct a result object.
- [BREAKING] Refactored the ``SearchIndex`` class to now be the ``TextIndex`` class.  Also renamed the ``CloudantDatabase`` convenience methods of ``get_all_indexes``, ``create_index``, and ``delete_index`` as ``get_query_indexes``, ``create_query_index``, and ``delete_query_index`` respectively.  These changes were made to clarify that the changed class and the changed methods were specific to query index processing only.
- [BREAKING] Replace "session" and "url" feed constructor arguments with "source" which can be either a client or a database object.  Changes also made to the client ``db_updates`` method signature and the database ``changes`` method signature.
- [BREAKING] Fixed ``CloudantDatabase.share_database`` to accept all valid permission roles.  Changed the method signature to accept roles as a list argument.
- [BREAKING] Removed credentials module from the API and moved it to the tests folder since the functionality is outside of the scope of this library but is still be useful in unit/integration tests.
- [IMPROVED] Changed the handling of queries using the keys argument to issue a http POST request instead of a http GET request so that the request is no longer bound by any URL length limitation.
- [IMPROVED] Added support for Result/QueryResult data access via index value and added validation logic to ``Result.__getitem__()``.
- [IMPROVED] Updated feed functionality to process ``_changes`` and ``_db_updates`` with their supported options.  Also added an infinite feed option.
- [NEW] Handled HTTP status code ``429 Too Many Requests`` with blocking backoff and retries.
- [NEW] Added support for CouchDB Admin Party mode.  This library can now be used with CouchDB instances where everyone is Admin.
- [FIX] Fixed ``Document.get_attachment`` method to successfully create text and binary files based on http response Content-Type.  The method also returns text, binary, and json content based on http response Content-Type.
- [FIX] Added validation to ``Cloudant.bill``, ``Cloudant.volume_usage``, and ``Cloudant.requests_usage`` methods to ensure that a valid year/month combination or neither are used as arguments.
- [FIX] Fixed the handling of empty views in the DesignDocument.
- [FIX] The ``CouchDatabase.create_document`` method now handles documents and design documents correctly.  If the document created is a design document then the locally cached object will be a DesignDocument otherwise it will be a Document.
- [CHANGE] Moved internal ``Code`` class, functions like ``python_to_couch`` and ``type_or_none``, and constants into a _common_util module.
- [CHANGE] Updated User-Agent header format to be ``python-cloudant/<library version>/Python/<Python version>/<OS name>/<OS architecture>``.
- [CHANGE] Completed the addition of unit tests that target a database server.  Removed all mocked unit tests.

2.0.0b2 (2016-02-24)
====================
- [FIX] Remove the fields parameter from required Query parameters.
- [NEW] Add Python 3 support.

2.0.0b1 (2016-01-11)
====================

- [NEW] Added support for Cloudant Query execution.
- [NEW] Added support for Cloudant Query index management.
- [FIX] DesignDocument content is no longer limited to just views.
- [FIX] Document url encoding is now enforced.
- [FIX] Database iterator now yields Document/DesignDocument objects with valid document urls.

2.0.0a4 (2015-12-03)
====================

- [FIX] Fixed incorrect readme reference to current library being Alpha 2.

2.0.0a3 (2015-12-03)
====================

- [NEW] Added API documentation hosted on readthedocs.org.

2.0.0a2 (2015-11-19)
====================

- [NEW] Added unit tests targeting CouchDB and Cloudant databases.
- [FIX] Fixed bug in database create validation check to work if response code is either 201 (created) or 202 (accepted).
- [FIX] Fixed database iterator infinite loop problem and to now yield a Document object.
- [BREAKING] Removed previous bulk_docs method from the CouchDatabase class and renamed the previous bulk_insert method as bulk_docs.  The previous bulk_docs functionality is available through the all_docs method using the "keys" parameter.
- [FIX] Made missing_revisions, revisions_diff, get_revision_limit, set_revision_limit, and view_cleanup API methods available for CouchDB as well as Cloudant.
- [BREAKING] Moved the db_update method to the account module.
- [FIX] Fixed missing_revisions to key on 'missing_revs'.
- [FIX] Fixed set_revision_limit to encode the request data payload correctly.
- [FIX] ``Document.create()`` will no longer update an existing document.
- [BREAKING] Renamed Document ``field_append`` method to ``list_field_append``.
- [BREAKING] Renamed Document ``field_remove`` method to ``list_field_remove``.
- [BREAKING] Renamed Document ``field_replace`` method to ``field_set``.
- [FIX] The Document local dictionary ``_id`` key is now synched with ``_document_id`` private attribute.
- [FIX] The Document local dictionary is now refreshed after an add/update/delete of an attachment.
- [FIX] The Document ``fetch()`` method now refreshes the Document local dictionary content correctly.
- [BREAKING] Replace the ReplicatorDatabase class with the Replicator class.  A Replicator object has a database attribute that represents the _replicator database.  This allows the Replicator to work for both a CloudantDatabase and a CouchDatabase.
- [REMOVED] Removed "not implemented" methods from the DesignDocument.
- [FIX] Add implicit "_design/" prefix for DesignDocument document ids.

2.0.0a1 (2015-10-13)
====================

- Initial release (2.0.0a1).
