# Migrating to the `cloudant-python-sdk` library
This document is to assist in migrating from the `python-cloudant` (module: `cloudant`) to the newly supported [`cloudant-python-sdk`](https://github.com/IBM/cloudant-python-sdk) (module: `ibmcloudant`).

## Initializing the client connection
There are several ways to create a client connection in `cloudant-python-sdk`:
1. [Environment variables](https://github.com/IBM/cloudant-python-sdk#authentication-with-environment-variables)
2. [External configuration file](https://github.com/IBM/cloudant-python-sdk#authentication-with-external-configuration)
3. [Programmatically](https://github.com/IBM/cloudant-python-sdk#programmatic-authentication)

[See the README](https://github.com/IBM/cloudant-python-sdk#code-examples) for code examples on using environment variables.

## Other differences
1. The `cloudant-python-sdk` library does not support local dictionary caching of database and document objects.
1. There are no context managers in `cloudant-python-sdk`. To reproduce the behaviour of the `python-cloudant`
context managers in `cloudant-python-sdk` users need to explicitly call the specific operations against the
remote HTTP API. For example, in the case of the document context manager, this would mean doing both a `get_document`
to fetch and a `put_document` to save.
1. In `cloudant-python-sdk` View, Search, and Query (aka `_find` endpoint) operation responses contain raw JSON
content like using `raw_result=True` in `python-cloudant`.
1. Replay adapters are replaced by the [automatic retries](https://github.
   com/IBM/ibm-cloud-sdk-common/#automatic-retries) feature for failed requests.
1. Error handling is not transferable from `python-cloudant` to `cloudant-python-sdk`. For more information go to the [Error handling section](https://cloud.ibm.com/apidocs/cloudant?code=python#error-handling) in our API docs.
1. Custom HTTP client configurations in `python-cloudant` are not transferable to `python-java-sdk`. For more information go to the [Configuring the HTTP client section(https://githubcom/IBM/ibm-cloud-sdk-common/#configuring-the-http-client) in the IBM Cloud SDK Common README.

## Request mapping
Here's a list of the top 5 most frequently used `python-cloudant` operations and the `cloudant-python-sdk` equivalent API operation documentation link:

| `python-cloudant` operation           | `cloudant-python-sdk` API operation documentation link |
|---------------------------------------|---------------------------------|
|`Document('db_name', 'docid').fetch()` |[`getDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdocument)|
|`db.get_view_result()`                 |[`postView`](https://cloud.ibm.com/apidocs/cloudant?code=python#postview)|
|`db.get_query_result()`                |[`postFind`](https://cloud.ibm.com/apidocs/cloudant?code=python#postfind)|
| `doc.exists()`                        |[`headDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#headdocument)|
|`Document('db_name', 'docid').save()`  |[`putDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#putdocument)|


[A table](#reference-table) with the whole list of operations is provided at the end of this guide.

The `cloudant-python-sdk` library is generated from a more complete API spec and provides a significant number of operations that do not exist in `python-cloudant`. See [the IBM Cloud API Documentation](https://cloud.ibm.com/apidocs/cloudant) to review request parameter and body options, code examples, and additional details for every endpoint.

## Known Issues
There's an [outline of known issues](https://github.com/IBM/cloudant-python-sdk/blob/master/KNOWN_ISSUES.md) in the `cloudant-python-sdk` repository.

## Reference table
The table below contains a list of `python-cloudant` functions and the `cloudant-python-sdk` equivalent API operation documentation link.  The `cloudant-python-sdk` operation documentation link will contain the new function in a code sample e.g. `getServerInformation` link will contain a code example with `get_server_information()`.

**Note:** There are many API operations included in the new `cloudant-python-sdk` that are not available in the `python-cloudant` library. The [API documentation](https://cloud.ibm.com/apidocs/cloudant?code=python) contains the full list of operations.

| `python-cloudant` function | `cloudant-python-sdk` API operation documentation link |
|-----------------|---------------------|
|`metadata()`|[`getServerInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getserverinformation)|
|`all_dbs()`|[`getAllDbs`](https://cloud.ibm.com/apidocs/cloudant?code=python#getalldbs)|
|`db_updates()/infinite_db_updates()`|[`getDbUpdates`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdbupdates)|
|`Replicator.stop_replication()`|[`deleteReplicationDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#deletereplicationdocument)|
|`Replicator.replication_state()`|[`getReplicationDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getreplicationdocument)|
|`Replicator.create_replication()`|[`putReplicationDocument`](https://cloud.ibm.com/apidocs/cloudant?code=#putreplicationdocument)|
|`Scheduler.get_doc()`|[`getSchedulerDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getschedulerdocument)|
|`Scheduler.list_docs()`|[`getSchedulerDocs`](https://cloud.ibm.com/apidocs/cloudant?code=python#getschedulerdocs)|
|`Scheduler.list_jobs()`|[`getSchedulerJobs`](https://cloud.ibm.com/apidocs/cloudant?code=python#getschedulerjobs)|
|`session()`|[`getSessionInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getsessioninformation)|
|`uuids()`|[`getUuids`](https://cloud.ibm.com/apidocs/cloudant?code=python#getuuids)|
|`db.delete()`|[`deleteDatabase`](https://cloud.ibm.com/apidocs/cloudant?code=python#deletedatabase)|
|`db.metadata()`|[`getDatabaseInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdatabaseinformation)|
|`db.create_document()`|[`postDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#postdocument)|
|`db.create()`|[`putDatabase`](https://cloud.ibm.com/apidocs/cloudant?code=python#putdatabase)|
|`db.all_docs()/db.keys()`|[`postAllDocs`](https://cloud.ibm.com/apidocs/cloudant?code=python#postalldocs)|
|`db.bulk_docs()`|[`postBulkDocs`](https://cloud.ibm.com/apidocs/cloudant?code=python#postbulkdocs)|
|`db.changes()/db.infinite_changes()`|[`postChanges`](https://cloud.ibm.com/apidocs/cloudant?code=python#postchanges-databases)|
|`DesignDocument(db, '_design/doc').delete()`|[`deleteDesignDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#deletedesigndocument)|
|`db.get_design_document()/DesignDocument(db, '_design/doc').fetch()`|[`getDesignDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdesigndocument)|
|`DesignDocument(db, '_design/doc').save()`|[`putDesignDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#putdesigndocument)|
|`DesignDocument(db, '_design/doc').info()`|[`getDesignDocumentInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdesigndocumentinformation)|
|`db.get_search_result()`|[`postSearch`](https://cloud.ibm.com/apidocs/cloudant?code=python#postsearch)|
|`db.get_view_result()`|[`postView`](https://cloud.ibm.com/apidocs/cloudant?code=python#postview)|
|`db.list_design_documents()`|[`postDesignDocs`](https://cloud.ibm.com/apidocs/cloudant?code=python#postdesigndocs)|
|`db.get_query_result()`|[`postFind`](https://cloud.ibm.com/apidocs/cloudant?code=python#postfind)|
|`db.get_query_indexes()`|[`getIndexesInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getindexesinformation)|
|`db.create_query_index()`|[`postIndex`](https://cloud.ibm.com/apidocs/cloudant?code=python#postindex)|
|`db.delete_query_index()`|[`deleteIndex`](https://cloud.ibm.com/apidocs/cloudant?code=python#deleteindex)|
|`Document(db, '_local/docid').fetch()`|[`getLocalDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getlocaldocument)|
|`Document(db, '_local/docid').save()`|[`putLocalDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#putlocaldocument)|
|`Document(db, '_local/docid').delete()`|[`deleteLocalDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#deletelocaldocument)|
|`db.missing_revisions()/db.revisions_diff()`|[`postRevsDiff`](https://cloud.ibm.com/apidocs/cloudant?code=python#postrevsdiff)|
|`db.partition_metadata()`|[`getPartitionInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getpartitioninformation)|
|`db.partitioned_all_docs()`|[`postPartitionAllDocs`](https://cloud.ibm.com/apidocs/cloudant?code=python#postpartitionalldocs)|
|`db.get_partitioned_search_result()`|[`postPartitionSearch`](https://cloud.ibm.com/apidocs/cloudant?code=python#postpartitionsearch)|
|`db.get_partitioned_view_result()`|[`postPartitionView`](https://cloud.ibm.com/apidocs/cloudant?code=python#postpartitionview)|
|`db.get_partitioned_query_result()`|[`postPartitionFind`](https://cloud.ibm.com/apidocs/cloudant?code=python#postpartitionfind-partitioned-databases)|
|`db.get_security_document()/db.security_document()`|[`getSecurity`](https://cloud.ibm.com/apidocs/cloudant?code=python#getsecurity)|
|`db.share_database()`|[`putSecurity`](https://cloud.ibm.com/apidocs/cloudant?code=python#putsecurity)|
|`db.shards()`|[`getShardsInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getshardsinformation)|
|`Document(db, 'docid').delete()`|[`deleteDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#deletedocument)|
|`Document(db, 'docid').fetch()`|[`getDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#getdocument)|
|`Document(db, 'docid').exists()`|[`headDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#headdocument)|
|`Document(db, 'docid').save()`|[`putDocument`](https://cloud.ibm.com/apidocs/cloudant?code=python#putdocument)|
|`Document(db, 'docid').delete_attachment()`|[`deleteAttachment`](https://cloud.ibm.com/apidocs/cloudant?code=python#deleteattachment)|
|`Document(db, 'docid').get_attachment()`|[`getAttachment`](https://cloud.ibm.com/apidocs/cloudant?code=python#getattachment)|
|`Document(db, 'docid').put_attachment()`|[`putAttachment`](https://cloud.ibm.com/apidocs/cloudant?code=python#putattachment)|
|`generate_api_key()`|[`postApiKeys`](https://cloud.ibm.com/apidocs/cloudant?code=python#postapikeys)|
|`SecurityDocument().save()`|[`putCloudantSecurityConfiguration`](https://cloud.ibm.com/apidocs/cloudant?code=python#putcloudantsecurity)|
|`cors_configuration()/cors_origin()`|[`getCorsInformation`](https://cloud.ibm.com/apidocs/cloudant?code=python#getcorsinformation)|
|`update_cors_configuration()`|[`putCorsConfiguration`](https://cloud.ibm.com/apidocs/cloudant?code=python#putcorsconfiguration)|
