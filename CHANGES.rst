2.0.0a2 (Unreleased)
====================

- [NEW] Added unit tests targeting CouchDB and Cloudant databases.
- [FIX] Fixed bug in database create validation check to work if response code
is either 201 (created) or 202 (accepted).
- [FIX] Fixed database iterator infinite loop problem and to now yield a 
Document object.
- [BREAKING] Removed previous bulk_docs method from the CouchDatabase class and 
renamed the previous bulk_insert method as bulk_docs.  The previous bulk_docs
functionality is available through the all_docs method using the "keys"
parameter.


2.0.0a1 (2015-10-13)
====================

- Initial release (2.0.0a1).
