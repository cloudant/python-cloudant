# Unreleased

- [NEW] Add `Document._transform` and `Document._detransform` methods.
- [NEW] Add new view parameters, `stable` and `update`, as keyword arguments to `get_view_result`.
- [FIXED] Case where an exception was raised after successful retry when using `doc.update_field`.

# 2.9.0 (2018-06-13)

- [NEW] Added functionality to test if a key is in a database as in `key in db`, overriding dict `__contains__` and checking in the remote database.
- [NEW] Moved `create_query_index` and other query related methods to `CouchDatabase` as the `_index`/`_find` API is available in CouchDB 2.x.
- [NEW] Support IAM authentication in replication documents.
- [FIXED] Case where `Document` context manager would throw instead of creating a new document if no `_id` was provided.
- [IMPROVED] Added support for IAM API key in `cloudant_bluemix` method.
- [IMPROVED] Shortened length of client URLs by removing username and password.
- [IMPROVED] Verified library operation on Python 3.6.3.

# 2.8.1 (2018-02-16)

- [FIXED] Installation failures of 2.8.0 caused by missing VERSION file in distribution.

# 2.8.0 (2018-02-15)

- [NEW] Added support for `/_search_disk_size` endpoint which retrieves disk size information for a specific search index.
- [FIXED] Updated default IBM Cloud Identity and Access Management token URL.
- [REMOVED] Removed broken source and target parameters that constantly threw `AttributeError` when creating a replication document.

# 2.7.0 (2017-10-31)

- [NEW] Added API for upcoming Bluemix Identity and Access Management support for Cloudant on Bluemix. Note: IAM API key support is not yet enabled in the service.
- [NEW] Added HTTP basic authentication support.
- [NEW] Added `Result.all()` convenience method.
- [NEW] Allow `service_name` to be specified when instantiating from a Bluemix VCAP_SERVICES environment variable.
- [IMPROVED] Updated `posixpath.join` references to use `'/'.join` when concatenating URL parts.
- [IMPROVED] Updated documentation by replacing deprecated Cloudant links with the latest Bluemix links.

# 2.6.0 (2017-08-10)

- [NEW] Added `Cloudant.bluemix()` class method to the Cloudant client allowing service credentials to be passed using the CloudFoundry VCAP_SERVICES environment variable.
- [FIXED] Fixed client construction in `cloudant_bluemix` context manager.
- [FIXED] Fixed validation for feed options to accept zero as a valid value.

# 2.5.0 (2017-07-06)

- [FIXED] Fixed crash caused by non-UTF8 chars in design documents.
- [FIXED] Fixed `TypeError` when setting revision limits on Python>=3.6.
- [FIXED] Fixed the `exists()` double check on `client.py` and `database.py`.
- [FIXED] Fixed Cloudant exception code 409 with 412 when creating a database that already exists.
- [FIXED] Catch error if `throw_on_exists` flag is `False` for creating a document.
- [FIXED] Fixed /_all_docs call where `keys` is an empty list.
- [FIXED] Issue where docs with IDs that sorted lower than 0 were not returned when iterating through _all_docs.

# 2.4.0 (2017-02-14)

- [NEW] Added `timeout` option to the client constructor for setting a timeout on a HTTP connection or a response.
- [NEW] Added `cloudant_bluemix` method to the Cloudant client allowing service credentials to be passed using the CloudFoundry VCAP_SERVICES environment variable.
- [IMPROVED] Updated non-response related errors with additional status code and improved error message for easier debugging.
  All non-response error are handled using either CloudantException or CloudantArgumentError.
- [FIXED] Support `long` type argument when executing in Python 2.

# 2.3.1 (2016-11-30)

- [FIXED] Resolved issue where generated UUIDs for replication documents would not be converted to strings.
- [FIXED] Resolved issue where CouchDatabase.infinite_changes() method can cause a stack overflow.

# 2.3.0 (2016-11-02)

- [FIXED] Resolved issue where the custom JSON encoder was at times not used when transforming data.
- [NEW] Added support for managing the database security document through the SecurityDocument class and CouchDatabase convenience method `get_security_document`.
- [NEW] Added `auto_renewal` option to the client constructor to handle the automatic renewal of an expired session cookie auth.

# 2.2.0 (2016-10-20)

- [NEW] Added auto connect feature to the client constructor. 
- [FIXED] Requests session is no longer valid after disconnect.

# 2.1.1 (2016-10-03)

- [FIXED] HTTPError is now raised when 4xx or 5xx codes are encountered.

# 2.1.0 (2016-08-31)

- [NEW] Added support for Cloudant Search execution.
- [NEW] Added support for Cloudant Search index management.
- [NEW] Added support for managing and querying list functions.
- [NEW] Added support for managing and querying show functions.
- [NEW] Added support for querying update handlers.
- [NEW] Added `rewrites` accessor property for URL rewriting.
- [NEW] Added `st_indexes` accessor property for Cloudant Geospatial indexes.
- [NEW] Added support for DesignDocument `_info` and `_search_info` endpoints.
- [NEW] Added `validate_doc_update` accessor property for update validators.
- [NEW] Added support for a custom `requests.HTTPAdapter` to be configured using an optional `adapter` arg e.g.
  `Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME, adapter=Replay429Adapter())`.
- [IMPROVED] Made the 429 response code backoff optional and configurable. To enable the backoff add
  an `adapter` arg of a `Replay429Adapter` with the desired number of retries and initial backoff. To replicate
  the 2.0.0 behaviour use: `adapter=Replay429Adapter(retries=10, initialBackoff=0.25)`. If `retries` or
  `initialBackoff` are not specified they will default to 3 retries and a 0.25 s initial backoff.
- [IMPROVED] Additional error reason details appended to HTTP response message errors.
- [FIX] `415 Client Error: Unsupported Media Type` when using keys with `db.all_docs`.
- [FIX] Allowed strings as well as lists for search `group_sort` arguments.

# 2.0.3 (2016-06-03)

- [FIX] Fixed the python-cloudant readthedocs documentation home page to resolve correctly.

# 2.0.2 (2016-06-02)

- [IMPROVED] Updated documentation links from python-cloudant.readthedocs.org to python-cloudant.readthedocs.io.
- [FIX] Fixed issue with Windows platform compatibility,replaced usage of os.uname for the user-agent string.
- [FIX] Fixed readthedocs link in README.rst to resolve to documentation home page.

# 2.0.1 (2016-06-02)

- [IMPROVED] Updated documentation links from python-cloudant.readthedocs.org to python-cloudant.readthedocs.io.
- [FIX] Fixed issue with Windows platform compatibility,replaced usage of os.uname for the user-agent string.
- [FIX] Fixed readthedocs link in README.rst to resolve to documentation home page.

# 2.0.0 (2016-05-02)

- [BREAKING] Renamed modules account.py, errors.py, indexes.py, views.py, to client.py, error.py, index.py, and view.py.
- [BREAKING] Removed the `make_result` method from `View` and `Query` classes.  If you need to make a query or view result, use `CloudantDatabase.get_query_result`, `CouchDatabase.get_view_result`, or the `View.custom_result` context manager.  Additionally, the `Result` and `QueryResult` classes can be called directly to construct a result object.
- [BREAKING] Refactored the `SearchIndex` class to now be the `TextIndex` class.  Also renamed the `CloudantDatabase` convenience methods of `get_all_indexes`, `create_index`, and `delete_index` as `get_query_indexes`, `create_query_index`, and `delete_query_index` respectively.  These changes were made to clarify that the changed class and the changed methods were specific to query index processing only.
- [BREAKING] Replace "session" and "url" feed constructor arguments with "source" which can be either a client or a database object.  Changes also made to the client `db_updates` method signature and the database `changes` method signature.
- [BREAKING] Fixed `CloudantDatabase.share_database` to accept all valid permission roles.  Changed the method signature to accept roles as a list argument.
- [BREAKING] Removed credentials module from the API and moved it to the tests folder since the functionality is outside of the scope of this library but is still be useful in unit/integration tests.
- [IMPROVED] Changed the handling of queries using the keys argument to issue a http POST request instead of a http GET request so that the request is no longer bound by any URL length limitation.
- [IMPROVED] Added support for Result/QueryResult data access via index value and added validation logic to `Result.__getitem__()`.
- [IMPROVED] Updated feed functionality to process `_changes` and `_db_updates` with their supported options.  Also added an infinite feed option.
- [NEW] Handled HTTP status code `429 Too Many Requests` with blocking backoff and retries.
- [NEW] Added support for CouchDB Admin Party mode.  This library can now be used with CouchDB instances where everyone is Admin.
- [FIX] Fixed `Document.get_attachment` method to successfully create text and binary files based on http response Content-Type.  The method also returns text, binary, and json content based on http response Content-Type.
- [FIX] Added validation to `Cloudant.bill`, `Cloudant.volume_usage`, and `Cloudant.requests_usage` methods to ensure that a valid year/month combination or neither are used as arguments.
- [FIX] Fixed the handling of empty views in the DesignDocument.
- [FIX] The `CouchDatabase.create_document` method now handles documents and design documents correctly.  If the document created is a design document then the locally cached object will be a DesignDocument otherwise it will be a Document.
- [CHANGE] Moved internal `Code` class, functions like `python_to_couch` and `type_or_none`, and constants into a _common_util module.
- [CHANGE] Updated User-Agent header format to be `python-cloudant/<library version>/Python/<Python version>/<OS name>/<OS architecture>`.
- [CHANGE] Completed the addition of unit tests that target a database server.  Removed all mocked unit tests.

# 2.0.0b2 (2016-02-24)

- [FIX] Remove the fields parameter from required Query parameters.
- [NEW] Add Python 3 support.

# 2.0.0b1 (2016-01-11)


- [NEW] Added support for Cloudant Query execution.
- [NEW] Added support for Cloudant Query index management.
- [FIX] DesignDocument content is no longer limited to just views.
- [FIX] Document url encoding is now enforced.
- [FIX] Database iterator now yields Document/DesignDocument objects with valid document urls.

# 2.0.0a4 (2015-12-03)


- [FIX] Fixed incorrect readme reference to current library being Alpha 2.

# 2.0.0a3 (2015-12-03)


- [NEW] Added API documentation hosted on readthedocs.org.

# 2.0.0a2 (2015-11-19)


- [NEW] Added unit tests targeting CouchDB and Cloudant databases.
- [FIX] Fixed bug in database create validation check to work if response code is either 201 (created) or 202 (accepted).
- [FIX] Fixed database iterator infinite loop problem and to now yield a Document object.
- [BREAKING] Removed previous bulk_docs method from the CouchDatabase class and renamed the previous bulk_insert method as bulk_docs.  The previous bulk_docs functionality is available through the all_docs method using the "keys" parameter.
- [FIX] Made missing_revisions, revisions_diff, get_revision_limit, set_revision_limit, and view_cleanup API methods available for CouchDB as well as Cloudant.
- [BREAKING] Moved the db_update method to the account module.
- [FIX] Fixed missing_revisions to key on 'missing_revs'.
- [FIX] Fixed set_revision_limit to encode the request data payload correctly.
- [FIX] `Document.create()` will no longer update an existing document.
- [BREAKING] Renamed Document `field_append` method to `list_field_append`.
- [BREAKING] Renamed Document `field_remove` method to `list_field_remove`.
- [BREAKING] Renamed Document `field_replace` method to `field_set`.
- [FIX] The Document local dictionary `_id` key is now synched with `_document_id` private attribute.
- [FIX] The Document local dictionary is now refreshed after an add/update/delete of an attachment.
- [FIX] The Document `fetch()` method now refreshes the Document local dictionary content correctly.
- [BREAKING] Replace the ReplicatorDatabase class with the Replicator class.  A Replicator object has a database attribute that represents the _replicator database.  This allows the Replicator to work for both a CloudantDatabase and a CouchDatabase.
- [REMOVED] Removed "not implemented" methods from the DesignDocument.
- [FIX] Add implicit "_design/" prefix for DesignDocument document ids.

# 2.0.0a1 (2015-10-13)


- Initial release (2.0.0a1).
