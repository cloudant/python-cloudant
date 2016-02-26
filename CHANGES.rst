2.0.0 (Unreleased)
==================
- [FIX] Fixed the handling of empty views in the DesignDocument.
- [BREAKING] Fixed CloudantDatabase.share_database to accept all valid permission roles.  Changed the method signature to accept roles as a list argument.

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
