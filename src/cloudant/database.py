#!/usr/bin/env python
# Copyright (c) 2015 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License a
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
API module that maps to a Cloudant or CouchDB database instance.
"""
import json
import contextlib
import posixpath

from requests.exceptions import HTTPError

from ._2to3 import url_quote_plus, iteritems_
from ._common_util import (
    JSON_INDEX_TYPE,
    SEARCH_INDEX_ARGS,
    SPECIAL_INDEX_TYPE,
    TEXT_INDEX_TYPE,
    get_docs)
from .document import Document
from .design_document import DesignDocument
from .view import View
from .index import Index, TextIndex, SpecialIndex
from .query import Query
from .error import CloudantException, CloudantArgumentError
from .result import Result, QueryResult
from .feed import Feed, InfiniteFeed

class CouchDatabase(dict):
    """
    Encapsulates a CouchDB database.  A CouchDatabase object is
    instantiated with a reference to a client/session.
    It supports accessing the documents, and various database
    features such as the document indexes, changes feed, design documents, etc.

    :param CouchDB client: Client instance used by the database.
    :param str database_name: Database name used to reference the database.
    :param int fetch_limit: Optional fetch limit used to set the max number of
        documents to fetch per query during iteration cycles.  Defaults to 100.
    """
    def __init__(self, client, database_name, fetch_limit=100):
        super(CouchDatabase, self).__init__()
        self.client = client
        self._database_host = client.server_url
        self.database_name = database_name
        self._fetch_limit = fetch_limit
        self.result = Result(self.all_docs)

    @property
    def r_session(self):
        """
        Returns the ``r_session`` from the client instance used by the database.

        :returns: Client ``r_session``
        """
        return self.client.r_session

    @property
    def admin_party(self):
        """
        Returns the CouchDB Admin Party status.  ``True`` if using Admin Party
        ``False`` otherwise.

        :returns: CouchDB Admin Party mode status
        """
        return self.client.admin_party

    @property
    def database_url(self):
        """
        Constructs and returns the database URL.

        :returns: Database URL
        """
        return posixpath.join(
            self._database_host,
            url_quote_plus(self.database_name)
        )

    @property
    def creds(self):
        """
        Retrieves a dictionary of useful authentication information
        that can be used to authenticate against this database.

        :returns: Dictionary containing authentication information
        """
        if self.admin_party:
            return None
        return {
            "basic_auth": self.client.basic_auth_str(),
            "user_ctx": self.client.session()['userCtx']
        }

    def exists(self):
        """
        Performs an existence check on the remote database.

        :returns: Boolean True if the database exists, False otherwise
        """
        resp = self.r_session.head(self.database_url)
        if resp.status_code not in [200, 404]:
            resp.raise_for_status()

        return resp.status_code == 200

    def metadata(self):
        """
        Retrieves the remote database metadata dictionary.

        :returns: Dictionary containing database metadata details
        """
        resp = self.r_session.get(self.database_url)
        resp.raise_for_status()
        return resp.json()

    def doc_count(self):
        """
        Retrieves the number of documents in the remote database

        :returns: Database document count
        """
        return self.metadata().get('doc_count')

    def create_document(self, data, throw_on_exists=False):
        """
        Creates a new document in the remote and locally cached database, using
        the data provided.  If an _id is included in the data then depending on
        that _id either a :class:`~cloudant.document.Document` or a
        :class:`~cloudant.design_document.DesignDocument`
        object will be added to the locally cached database and returned by this
        method.

        :param dict data: Dictionary of document JSON data, containing _id.
        :param bool throw_on_exists: Optional flag dictating whether to raise
            an exception if the document already exists in the database.

        :returns: A :class:`~cloudant.document.Document` or
            :class:`~cloudant.design_document.DesignDocument` instance
            corresponding to the new document in the database.
        """
        docid = data.get('_id', None)
        doc = None
        if docid and docid.startswith('_design/'):
            doc = DesignDocument(self, docid)
        else:
            doc = Document(self, docid)
        if throw_on_exists and doc.exists():
            raise CloudantException(
                'Error - Document with id {0} already exists.'.format(docid)
            )
        doc.update(data)
        doc.create()
        super(CouchDatabase, self).__setitem__(doc['_id'], doc)
        return doc

    def new_document(self):
        """
        Creates a new, empty document in the remote and locally cached database,
        auto-generating the _id.

        :returns: Document instance corresponding to the new document in the
            database
        """
        doc = Document(self, None)
        doc.create()
        super(CouchDatabase, self).__setitem__(doc['_id'], doc)
        return doc

    def design_documents(self):
        """
        Retrieve the JSON content for all design documents in this database.
        Performs a remote call to retrieve the content.

        :returns: All design documents found in this database in JSON format
        """
        url = posixpath.join(self.database_url, '_all_docs')
        query = "startkey=\"_design\"&endkey=\"_design0\"&include_docs=true"
        resp = self.r_session.get(url, params=query)
        resp.raise_for_status()
        data = resp.json()
        return data['rows']

    def list_design_documents(self):
        """
        Retrieves a list of design document names in this database.
        Performs a remote call to retrieve the content.

        :returns: List of names for all design documents in this database
        """
        url = posixpath.join(self.database_url, '_all_docs')
        query = "startkey=\"_design\"&endkey=\"_design0\""
        resp = self.r_session.get(url, params=query)
        resp.raise_for_status()
        data = resp.json()
        return [x.get('key') for x in data.get('rows', [])]

    def get_design_document(self, ddoc_id):
        """
        Retrieves a design document.  If a design document exists remotely
        then that content is wrapped in a DesignDocument object and returned
        to the caller.  Otherwise a "shell" DesignDocument object is returned.

        :param str ddoc_id: Design document id

        :returns: A DesignDocument instance, if exists remotely then it will
            be populated accordingly
        """
        ddoc = DesignDocument(self, ddoc_id)
        try:
            ddoc.fetch()
        except HTTPError as error:
            if error.response.status_code != 404:
                raise

        return ddoc

    def get_view_result(self, ddoc_id, view_name, raw_result=False, **kwargs):
        """
        Retrieves the view result based on the design document and view name.
        By default the result is returned as a
        :class:`~cloudant.result.Result` object which provides a key
        accessible, sliceable, and iterable interface to the result collection.
        Depending on how you are accessing, slicing or iterating through your
        result collection certain query parameters are not permitted.  See
        :class:`~cloudant.result.Result` for additional details.

        However, by setting ``raw_result=True``, the result will be returned as
        the raw JSON response content for the view requested.  With this setting
        there are no restrictions on the query parameters used but it also
        means that the result collection key access, slicing, and iteration is
        the responsibility of the developer.

        For example:

        .. code-block:: python

            # get Result based on a design document view
            result = db.get_view_result('_design/ddoc_id_001', 'view_001')

            # get a customized Result based on a design document view
            result = db.get_view_result('_design/ddoc_id_001', 'view_001',
                include_docs=True, reduce=False)

            # get raw response content based on a design document view
            result = db.get_view_result('_design/ddoc_id_001', 'view_001',
                raw_result=True)

            # get customized raw response content for a design document view
            db.get_view_result('_design/ddoc_id_001', 'view_001',
                raw_result=True, include_docs=True, skip=100, limit=100)

        For more detail on key access, slicing and iteration, refer to the
        :class:`~cloudant.result.Result` documentation.

        :param str ddoc_id: Design document id used to get result.
        :param str view_name: Name of the view used to get result.
        :param bool raw_result: Dictates whether the view result is returned
            as a default Result object or a raw JSON response.
            Defaults to False.
        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are lists. Groups reduce results for the specified number
            of list fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param key: Return only documents that match the specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param list keys: Return only documents that match the specified keys.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param int limit: Limit the number of returned documents to the
            specified count.  Not valid when used with
            :class:`~cloudant.result.Result` iteration.
        :param int page_size: Sets the page size for result iteration.
            Only valid if used with ``raw_result=False``.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param int skip: Skip this number of rows from the start.
            Not valid when used with :class:`~cloudant.result.Result` iteration.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: The result content either wrapped in a QueryResult or
            as the raw response JSON content
        """
        view = View(DesignDocument(self, ddoc_id), view_name)
        if raw_result:
            return view(**kwargs)
        elif kwargs:
            return Result(view, **kwargs)
        else:
            return view.result

    def create(self):
        """
        Creates a database defined by the current database object, if it
        does not already exist and raises a CloudantException if the operation
        fails.  If the database already exists then this method call is a no-op.

        :returns: The database object
        """
        if self.exists():
            return self

        resp = self.r_session.put(self.database_url)
        if resp.status_code == 201 or resp.status_code == 202:
            return self

        raise CloudantException(
            "Unable to create database {0}: Reason: {1}".format(
                self.database_url, resp.text
            ),
            code=resp.status_code
        )

    def delete(self):
        """
        Deletes the current database from the remote instance.
        """
        resp = self.r_session.delete(self.database_url)
        resp.raise_for_status()

    def all_docs(self, **kwargs):
        """
        Wraps the _all_docs primary index on the database, and returns the
        results by value. This can be used as a direct query to the _all_docs
        endpoint.  More convenient/efficient access using keys, slicing
        and iteration can be done through the ``result`` attribute.

        Keyword arguments supported are those of the view/index access API.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int limit: Limit the number of returned documents to the
            specified count.
        :param int skip: Skip this number of rows from the start.
        :param startkey: Return records starting with the specified key.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: Raw JSON response content from ``_all_docs`` endpoint

        """
        resp = get_docs(self.r_session,
                        '/'.join([self.database_url, '_all_docs']),
                        self.client.encoder,
                        **kwargs)
        return resp.json()

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        Provides a context manager that can be used to customize the
        ``_all_docs`` behavior and wrap the output as a
        :class:`~cloudant.result.Result`.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param key: Return only documents that match the specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param list keys: Return only documents that match the specified keys.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param int page_size: Sets the page size for result iteration.
        :param startkey: Return records starting with the specified key.
            Not valid when used with :class:`~cloudant.result.Result` key
            access and key slicing.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        For example:

        .. code-block:: python

            with database.custom_result(include_docs=True) as rslt:
                data = rslt[100: 200]
        """
        rslt = Result(self.all_docs, **options)
        yield rslt
        del rslt

    def keys(self, remote=False):
        """
        Retrieves the list of document ids in the database.  Default is
        to return only the locally cached document ids, specify remote=True
        to make a remote request to include all document ids from the remote
        database instance.

        :param bool remote: Dictates whether the list of locally cached
            document ids are returned or a remote request is made to include
            an up to date list of document ids from the server.
            Defaults to False.

        :returns: List of document ids
        """
        if not remote:
            return list(super(CouchDatabase, self).keys())
        docs = self.all_docs()
        return [row['id'] for row in docs.get('rows', [])]

    def changes(self, raw_data=False, **kwargs):
        """
        Returns the ``_changes`` feed iterator.  The ``_changes`` feed can be
        iterated over and once complete can also provide the last sequence
        identifier of the feed.  If necessary, the iteration can be stopped by
        issuing a call to the ``stop()`` method on the returned iterator object.

        For example:

        .. code-block:: python

            # Iterate over a "normal" _changes feed
            changes = db.changes()
            for change in changes:
                print(change)
            print(changes.last_seq)

            # Iterate over a "continuous" _changes feed with additional options
            changes = db.changes(feed='continuous', since='now', descending=True)
            for change in changes:
                if some_condition:
                    changes.stop()
                print(change)

        :param bool raw_data: If set to True then the raw response data will be
            streamed otherwise if set to False then JSON formatted data will be
            streamed.  Default is False.
        :param bool conflicts: Can only be set if include_docs is True. Adds
            information about conflicts to each document.  Default is False.
        :param bool descending: Changes appear in sequential order.  Default is
            False.
        :param list doc_ids: To be used only when ``filter`` is set to
            ``_doc_ids``. Filters the feed so that only changes to the
            specified documents are sent.
        :param str feed: Type of feed.  Valid values are ``continuous``,
            ``longpoll``, and ``normal``.  Default is ``normal``.
        :param str filter: Name of filter function from a design document to get
            updates.  Default is no filter.
        :param int heartbeat: Time in milliseconds after which an empty line is
            sent during ``longpoll`` or ``continuous`` if there have been no
            changes.  Must be a positive number.  Default is no heartbeat.
        :param bool include_docs: Include the document with the result.  The
            document will not be returned as a
            :class:`~cloudant.document.Document` but instead will be returned as
            either formated JSON or as raw response content.  Default is False.
        :param int limit: Maximum number of rows to return.  Must be a positive
            number.  Default is no limit.
        :param since: Start the results from changes after the specified
            sequence identifier. In other words, using since excludes from the
            list all changes up to and including the specified sequence
            identifier. If since is 0 (the default), or omitted, the request
            returns all changes. If it is ``now``, only changes made after the
            time of the request will be emitted.
        :param str style: Specifies how many revisions are returned in the
            changes array. The default, ``main_only``, only returns the current
            "winning" revision; ``all_docs`` returns all leaf revisions,
            including conflicts and deleted former conflicts.
        :param int timeout: Number of milliseconds to wait for data before
            terminating the response. ``heartbeat`` supersedes ``timeout`` if
            both are supplied.
        :param int chunk_size: The HTTP response stream chunk size.  Defaults to
            512.

        :returns: Feed object that can be iterated over as a ``_changes`` feed.
        """
        return Feed(self, raw_data, **kwargs)

    def infinite_changes(self, **kwargs):
        """
        Returns an infinite (perpetually refreshed) ``_changes`` feed iterator.
        If necessary, the iteration can be stopped by issuing a call to the
        ``stop()`` method on the returned iterator object.

        For example:

        .. code-block:: python

            # Iterate over an infinite _changes feed
            changes = db.infinite_changes()
            for change in changes:
                if some_condition:
                    changes.stop()
                print(change)

        :param bool conflicts: Can only be set if include_docs is True. Adds
            information about conflicts to each document.  Default is False.
        :param bool descending: Changes appear in sequential order.  Default is
            False.
        :param list doc_ids: To be used only when ``filter`` is set to
            ``_doc_ids``. Filters the feed so that only changes to the
            specified documents are sent.
        :param str filter: Name of filter function from a design document to get
            updates.  Default is no filter.
        :param int heartbeat: Time in milliseconds after which an empty line is
            sent if there have been no changes.  Must be a positive number.
            Default is no heartbeat.
        :param bool include_docs: Include the document with the result.  The
            document will not be returned as a
            :class:`~cloudant.document.Document` but instead will be returned as
            either formated JSON or as raw response content.  Default is False.
        :param since: Start the results from changes after the specified
            sequence identifier. In other words, using since excludes from the
            list all changes up to and including the specified sequence
            identifier. If since is 0 (the default), or omitted, the request
            returns all changes. If it is ``now``, only changes made after the
            time of the request will be emitted.
        :param str style: Specifies how many revisions are returned in the
            changes array. The default, ``main_only``, only returns the current
            "winning" revision; ``all_docs`` returns all leaf revisions,
            including conflicts and deleted former conflicts.
        :param int timeout: Number of milliseconds to wait for data before
            terminating the response. ``heartbeat`` supersedes ``timeout`` if
            both are supplied.
        :param int chunk_size: The HTTP response stream chunk size.  Defaults to
            512.

        :returns: Feed object that can be iterated over as a ``_changes`` feed.
        """
        return InfiniteFeed(self, **kwargs)

    def __getitem__(self, key):
        """
        Overrides dictionary __getitem__ behavior to provide a document
        instance for the specified key from the current database.

        If the document instance does not exist locally, then a remote request
        is made and the document is subsequently added to the local cache and
        returned to the caller.

        If the document instance already exists locally then it is returned and
        a remote request is not performed.

        A KeyError will result if the document does not exist locally or in the
        remote database.

        :param str key: Document id used to retrieve the document from the
            database.

        :returns: A Document or DesignDocument object depending on the
            specified document id (key)
        """
        if key in list(self.keys()):
            return super(CouchDatabase, self).__getitem__(key)
        if key.startswith('_design/'):
            doc = DesignDocument(self, key)
        else:
            doc = Document(self, key)
        if doc.exists():
            doc.fetch()
            super(CouchDatabase, self).__setitem__(key, doc)
            return doc
        else:
            raise KeyError(key)

    def __iter__(self, remote=True):
        """
        Overrides dictionary __iter__ behavior to provide iterable Document
        results.  By default, Documents are fetched from the remote database,
        in batches equal to the database object's defined ``fetch_limit``,
        yielding Document/DesignDocument objects.

        If ``remote=False`` then the locally cached Document objects are
        iterated over with no attempt to retrieve documents from the remote
        database.

        :param bool remote: Dictates whether the locally cached
            Document objects are returned or a remote request is made to
            retrieve Document objects from the remote database.
            Defaults to True.

        :returns: Iterable of Document and/or DesignDocument objects
        """
        if not remote:
            super(CouchDatabase, self).__iter__()
        else:
            next_startkey = '0'
            while next_startkey is not None:
                docs = self.all_docs(
                    limit=self._fetch_limit + 1,  # Get one extra doc
                                                  # to use as
                                                  # next_startkey
                    include_docs=True,
                    startkey=next_startkey
                ).get('rows', [])

                if len(docs) > self._fetch_limit:
                    next_startkey = docs.pop()['id']
                else:
                    # This is the last batch of docs, so we set
                    # ourselves up to break out of the while loop
                    # after this pass.
                    next_startkey = None

                for doc in docs:
                    # Wrap the doc dictionary as the appropriate
                    # document object before yielding it.
                    if doc['id'].startswith('_design/'):
                        document = DesignDocument(self, doc['id'])
                    else:
                        document = Document(self, doc['id'])
                    document.update(doc['doc'])
                    super(CouchDatabase, self).__setitem__(doc['id'], document)
                    yield document

            raise StopIteration

    def bulk_docs(self, docs):
        """
        Performs multiple document inserts and/or updates through a single
        request.  Each document must either be or extend a dict as
        is the case with Document and DesignDocument objects.  A document
        must contain the ``_id`` and ``_rev`` fields if the document
        is meant to be updated.

        :param list docs: List of Documents to be created/updated.

        :returns: Bulk document creation/update status in JSON format
        """
        url = posixpath.join(self.database_url, '_bulk_docs')
        data = {'docs': docs}
        headers = {'Content-Type': 'application/json'}
        resp = self.r_session.post(
            url,
            data=json.dumps(data),
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()

    def missing_revisions(self, doc_id, *revisions):
        """
        Returns a list of document revision values that do not exist in the
        current remote database for the specified document id and specified
        list of revision values.

        :param str doc_id: Document id to check for missing revisions against.
        :param list revisions: List of document revisions values to check
            against.

        :returns: List of missing document revision values
        """
        url = posixpath.join(self.database_url, '_missing_revs')
        data = {doc_id: list(revisions)}

        resp = self.r_session.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        resp.raise_for_status()

        resp_json = resp.json()
        missing_revs = resp_json['missing_revs'].get(doc_id)
        if missing_revs is None:
            missing_revs = []

        return missing_revs

    def revisions_diff(self, doc_id, *revisions):
        """
        Returns the differences in the current remote database for the specified
        document id and specified list of revision values.

        :param str doc_id: Document id to check for revision differences
            against.
        :param list revisions: List of document revisions values to check
            against.

        :returns: The revision differences in JSON format
        """
        url = posixpath.join(self.database_url, '_revs_diff')
        data = {doc_id: list(revisions)}

        resp = self.r_session.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        resp.raise_for_status()

        return resp.json()

    def get_revision_limit(self):
        """
        Retrieves the limit of historical revisions to store for any single
        document in the current remote database.

        :returns: Revision limit value for the current remote database
        """
        url = posixpath.join(self.database_url, '_revs_limit')
        resp = self.r_session.get(url)
        resp.raise_for_status()

        try:
            ret = int(resp.text)
        except ValueError:
            resp.status_code = 400
            raise CloudantException(
                'Error - Invalid Response Value: {}'.format(resp.json())
            )

        return ret

    def set_revision_limit(self, limit):
        """
        Sets the limit of historical revisions to store for any single document
        in the current remote database.

        :param int limit: Number of revisions to store for any single document
            in the current remote database.

        :returns: Revision limit set operation status in JSON format
        """
        url = posixpath.join(self.database_url, '_revs_limit')

        resp = self.r_session.put(url, data=json.dumps(limit))
        resp.raise_for_status()

        return resp.json()

    def view_cleanup(self):
        """
        Removes view files that are not used by any design document in the
        remote database.

        :returns: View cleanup status in JSON format
        """
        url = posixpath.join(self.database_url, '_view_cleanup')
        resp = self.r_session.post(
            url,
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()

        return resp.json()

    def get_list_function_result(self, ddoc_id, list_name, view_name, **kwargs):
        """
        Retrieves a customized MapReduce view result from the specified
        database based on the list function provided.  List functions are
        used, for example,  when you want to access Cloudant directly
        from a browser, and need data to be returned in a different
        format, such as HTML.

        Note: All query parameters for View requests are supported.
        See :class:`~cloudant.database.get_view_result` for
        all supported query parameters.

        For example:

        .. code-block:: python

            # Assuming that 'view001' exists as part of the
            # 'ddoc001' design document in the remote database...
            # Retrieve documents where the list function is 'list1'
            resp = db.get_list_result('ddoc001', 'list1', 'view001', limit=10)
            for row in resp['rows']:
                # Process data (in text format).

        For more detail on list functions, refer to the
        `Cloudant list documentation <https://docs.cloudant.com/
        design_documents.html#list-functions>`_.

        :param str ddoc_id: Design document id used to get result.
        :param str list_name: Name used in part to identify the
            list function.
        :param str view_name: Name used in part to identify the view.

        :return: Formatted view result data in text format
        """
        ddoc = DesignDocument(self, ddoc_id)
        headers = {'Content-Type': 'application/json'}
        resp = get_docs(self.r_session,
                        '/'.join([ddoc.document_url, '_list', list_name, view_name]),
                        self.client.encoder,
                        headers,
                        **kwargs)
        return resp.text

    def get_show_function_result(self, ddoc_id, show_name, doc_id):
        """
        Retrieves a formatted document from the specified database
        based on the show function provided.  Show functions, for example,
        are used when you want to access Cloudant directly from a browser,
        and need data to be returned in a different format, such as HTML.

        For example:

        .. code-block:: python

            # Assuming that 'view001' exists as part of the
            # 'ddoc001' design document in the remote database...
            # Retrieve a formatted 'doc001' document where the show function is 'show001'
            resp = db.get_show_function_result('ddoc001', 'show001', 'doc001')
            for row in resp['rows']:
                # Process data (in text format).

        For more detail on show functions, refer to the
        `Cloudant show documentation <https://docs.cloudant.com/
        design_documents.html#show-functions>`_.

        :param str ddoc_id: Design document id used to get the result.
        :param str show_name: Name used in part to identify the
            show function.
        :param str doc_id: The ID of the document to show.

        :return: Formatted document result data in text format
        """
        ddoc = DesignDocument(self, ddoc_id)
        headers = {'Content-Type': 'application/json'}
        resp = get_docs(self.r_session,
                        '/'.join([ddoc.document_url, '_show', show_name, doc_id]),
                        self.client.encoder,
                        headers)
        return resp.text

    def update_handler_result(self, ddoc_id, handler_name, doc_id=None, data=None, **params):
        """
        Creates or updates a document from the specified database based on the
        update handler function provided.  Update handlers are used, for
        example, to provide server-side modification timestamps, and document
        updates to individual fields without the latest revision. You can
        provide query parameters needed by the update handler function using
        the ``params`` argument.

        Create a document with a generated ID:

        .. code-block:: python

            # Assuming that 'update001' update handler exists as part of the
            # 'ddoc001' design document in the remote database...
            # Execute 'update001' to create a new document
            resp = db.update_handler_result('ddoc001', 'update001', data={'name': 'John',
                                            'message': 'hello'})

        Create or update a document with the specified ID:

        .. code-block:: python

            # Assuming that 'update001' update handler exists as part of the
            # 'ddoc001' design document in the remote database...
            # Execute 'update001' to update document 'doc001' in the database
            resp = db.update_handler_result('ddoc001', 'update001', 'doc001',
                                            data={'month': 'July'})

        For more details, see the `update handlers documentation
        <https://docs.cloudant.com/design_documents.html#update-handlers>`_.

        :param str ddoc_id: Design document id used to get result.
        :param str handler_name: Name used in part to identify the
            update handler function.
        :param str doc_id: Optional document id used to specify the
            document to be handled.

        :returns: Result of update handler function in text format
        """
        ddoc = DesignDocument(self, ddoc_id)
        if doc_id:
            resp = self.r_session.put(
                '/'.join([ddoc.document_url, '_update', handler_name, doc_id]),
                params=params, data=data)
        else:
            resp = self.r_session.post(
                '/'.join([ddoc.document_url, '_update', handler_name]),
                params=params, data=data)
        resp.raise_for_status()
        return resp.text

class CloudantDatabase(CouchDatabase):
    """
    Encapsulates a Cloudant database.  A CloudantDatabase object is
    instantiated with a reference to a client/session.
    It supports accessing the documents, and various database
    features such as the document indexes, changes feed, design documents, etc.

    :param Cloudant client: Client instance used by the database.
    :param str database_name: Database name used to reference the database.
    :param int fetch_limit: Optional fetch limit used to set the max number of
        documents to fetch per query during iteration cycles.  Defaults to 100.
    """
    def __init__(self, client, database_name, fetch_limit=100):
        super(CloudantDatabase, self).__init__(
            client,
            database_name,
            fetch_limit=fetch_limit
        )

    def security_document(self):
        """
        Retrieves the security document for the current database
        containing information about the users that the database
        is shared with.

        :returns: Security document in JSON format
        """
        resp = self.r_session.get(self.security_url)
        resp.raise_for_status()
        return resp.json()

    @property
    def security_url(self):
        """
        Constructs and returns the security document URL.

        :returns: Security document URL
        """
        parts = ['_api', 'v2', 'db', self.database_name, '_security']
        url = posixpath.join(self._database_host, *parts)
        return url

    def share_database(self, username, roles=None):
        """
        Shares the current remote database with the username provided.
        You can grant varying degrees of access rights,
        default is to share read-only, but additional
        roles can be added by providing the specific roles as a
        ``list`` argument.  If the user already has this database shared with
        them then it will modify/overwrite the existing permissions.

        :param str username: Cloudant user to share the database with.
        :param list roles: A list of
            `roles <https://docs.cloudant.com/authorization.html#roles>`_
            to grant to the named user.

        :returns: Share database status in JSON format
        """
        if roles is None:
            roles = ['_reader']
        valid_roles = [
            '_reader',
            '_writer',
            '_admin',
            '_replicator',
            '_db_updates',
            '_design',
            '_shards',
            '_security'
        ]
        doc = self.security_document()
        data = doc.get('cloudant', {})
        perms = []
        if all(role in valid_roles for role in roles):
            perms = list(set(roles))

        if not perms:
            msg = (
                'Invalid role(s) provided: {0}.  Valid roles are: {1}.'
            ).format(roles, valid_roles)
            raise CloudantArgumentError(msg)

        data[username] = perms
        doc['cloudant'] = data
        resp = self.r_session.put(
            self.security_url,
            data=json.dumps(doc),
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()
        return resp.json()

    def unshare_database(self, username):
        """
        Removes all sharing with the named user for the current remote database.
        This will remove the entry for the user from the security document.
        To modify permissions, use the
        :func:`~cloudant.database.CloudantDatabase.share_database` method
        instead.

        :param str username: Cloudant user to unshare the database from.

        :returns: Unshare database status in JSON format
        """
        doc = self.security_document()
        data = doc.get('cloudant', {})
        if username in data:
            del data[username]
        doc['cloudant'] = data
        resp = self.r_session.put(
            self.security_url,
            data=json.dumps(doc),
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()
        return resp.json()

    def shards(self):
        """
        Retrieves information about the shards in the current remote database.

        :returns: Shard information retrieval status in JSON format
        """
        url = posixpath.join(self.database_url, '_shards')
        resp = self.r_session.get(url)
        resp.raise_for_status()

        return resp.json()

    def get_query_indexes(self, raw_result=False):
        """
        Retrieves query indexes from the remote database.

        :param bool raw_result: If set to True then the raw JSON content for
            the request is returned.  Default is to return a list containing
            :class:`~cloudant.index.Index`,
            :class:`~cloudant.index.TextIndex`, and
            :class:`~cloudant.index.SpecialIndex` wrapped objects.

        :returns: The query indexes in the database
        """

        url = posixpath.join(self.database_url, '_index')
        resp = self.r_session.get(url)
        resp.raise_for_status()

        if raw_result:
            return resp.json()

        indexes = []
        for data in resp.json().get('indexes', []):
            if data.get('type') == JSON_INDEX_TYPE:
                indexes.append(Index(
                    self,
                    data.get('ddoc'),
                    data.get('name'),
                    **data.get('def', {})
                ))
            elif data.get('type') == TEXT_INDEX_TYPE:
                indexes.append(TextIndex(
                    self,
                    data.get('ddoc'),
                    data.get('name'),
                    **data.get('def', {})
                ))
            elif data.get('type') == SPECIAL_INDEX_TYPE:
                indexes.append(SpecialIndex(
                    self,
                    data.get('ddoc'),
                    data.get('name'),
                    **data.get('def', {})
                ))
            else:
                raise CloudantException('Unexpected index content: {0} found.')
        return indexes

    def create_query_index(
            self,
            design_document_id=None,
            index_name=None,
            index_type='json',
            **kwargs
    ):
        """
        Creates either a JSON or a text query index in the remote database.

        :param str index_type: The type of the index to create.  Can
            be either 'text' or 'json'.  Defaults to 'json'.
        :param str design_document_id: Optional identifier of the design
            document in which the index will be created. If omitted the default
            is that each index will be created in its own design document.
            Indexes can be grouped into design documents for efficiency.
            However, a change to one index in a design document will invalidate
            all other indexes in the same document.
        :param str index_name: Optional name of the index. If omitted, a name
            will be generated automatically.
        :param list fields: A list of fields that should be indexed.  For JSON
            indexes, the fields parameter is mandatory and should follow the
            'sort syntax'.  For example ``fields=['name', {'age': 'desc'}]``
            will create an index on the 'name' field in ascending order and the
            'age' field in descending order.  For text indexes, the fields
            parameter is optional.  If it is included then each field element
            in the fields list must be a single element dictionary where the
            key is the field name and the value is the field type.  For example
            ``fields=[{'name': 'string'}, {'age': 'number'}]``.  Valid field
            types are ``'string'``, ``'number'``, and ``'boolean'``.
        :param dict default_field: Optional parameter that specifies how the
            ``$text`` operator can be used with the index.  Only valid when
            creating a text index.
        :param dict selector: Optional parameter that can be used to limit the
            index to a specific set of documents that match a query. It uses
            the same syntax used for selectors in queries.  Only valid when
            creating a text index.

        :returns: An Index object representing the index created in the
            remote database
        """
        if index_type == JSON_INDEX_TYPE:
            index = Index(self, design_document_id, index_name, **kwargs)
        elif index_type == TEXT_INDEX_TYPE:
            index = TextIndex(self, design_document_id, index_name, **kwargs)
        else:
            msg = (
                'Invalid index type: {0}.  '
                'Index type must be either \"json\" or \"text\"'
            ).format(index_type)
            raise CloudantArgumentError(msg)
        index.create()
        return index

    def delete_query_index(self, design_document_id, index_type, index_name):
        """
        Deletes the query index identified by the design document id,
        index type and index name from the remote database.

        :param str design_document_id: The design document id that the index
            exists in.
        :param str index_type: The type of the index to be deleted.  Must
            be either 'text' or 'json'.
        :param str index_name: The index name of the index to be deleted.
        """
        if index_type == JSON_INDEX_TYPE:
            index = Index(self, design_document_id, index_name)
        elif index_type == TEXT_INDEX_TYPE:
            index = TextIndex(self, design_document_id, index_name)
        else:
            msg = (
                'Invalid index type: {0}.  '
                'Index type must be either \"json\" or \"text\"'
            ).format(index_type)
            raise CloudantArgumentError(msg)
        index.delete()

    def get_query_result(self, selector, fields=None, raw_result=False,
                         **kwargs):
        """
        Retrieves the query result from the specified database based on the
        query parameters provided.  By default the result is returned as a
        :class:`~cloudant.result.QueryResult` which uses the ``skip`` and
        ``limit`` query parameters internally to handle slicing and iteration
        through the query result collection.  Therefore ``skip`` and ``limit``
        cannot be used as arguments to get the query result when
        ``raw_result=False``.  However, by setting ``raw_result=True``, the
        result will be returned as the raw JSON response content for the query
        requested.  Using this setting requires the developer to manage their
        own slicing and iteration.  Therefore ``skip`` and ``limit`` are valid
        arguments in this instance.

        For example:

        .. code-block:: python

            # Retrieve documents where the name field is 'foo'
            selector = {'name': {'$eq': 'foo'}}
            docs = db.get_query_result(selector)
            for doc in docs:
                print doc

            # Retrieve documents sorted by the age field in ascending order
            docs = db.get_query_result(selector, sort=['name'])
            for doc in docs:
                print doc

            # Retrieve JSON response content, limiting response to 100 documents
            resp = db.get_query_result(selector, raw_result=True, limit=100)
            for doc in resp['docs']:
                print doc

        For more detail on slicing and iteration, refer to the
        :class:`~cloudant.result.QueryResult` documentation.

        :param str selector: Dictionary object describing criteria used to
            select documents.
        :param list fields: A list of fields to be returned by the query.
        :param bool raw_result: Dictates whether the query result is returned
            wrapped in a QueryResult or if the response JSON is returned.
            Defaults to False.
        :param str bookmark: A string that enables you to specify which page of
            results you require. Only valid for queries using indexes of type
            *text*.
        :param int limit: Maximum number of results returned.  Only valid if
            used with ``raw_result=True``.
        :param int page_size: Sets the page size for result iteration.  Default
            is 100.  Only valid with ``raw_result=False``.
        :param int r: Read quorum needed for the result.  Each document is read
            from at least 'r' number of replicas before it is returned in the
            results.
        :param int skip: Skip the first 'n' results, where 'n' is the value
            specified.  Only valid if used with ``raw_result=True``.
        :param list sort: A list of fields to sort by.  Optionally the list can
            contain elements that are single member dictionary structures that
            specify sort direction.  For example
            ``sort=['name', {'age': 'desc'}]`` means to sort the query results
            by the "name" field in ascending order and the "age" field in
            descending order.
        :param str use_index: Identifies a specific index for the query to run
            against, rather than using the Cloudant Query algorithm which finds
            what it believes to be the best index.

        :returns: The result content either wrapped in a QueryResult or
            as the raw response JSON content
        """
        if fields:
            query = Query(self, selector=selector, fields=fields)
        else:
            query = Query(self, selector=selector)
        if raw_result:
            return query(**kwargs)
        if kwargs:
            return QueryResult(query, **kwargs)
        else:
            return query.result

    def get_search_result(self, ddoc_id, index_name, **query_params):
        """
        Retrieves the raw JSON content from the remote database based on the
        search index on the server, using the query_params provided as query
        parameters. A ``query`` parameter containing the Lucene query
        syntax is mandatory.

        Example for search queries:

        .. code-block:: python

            # Assuming that 'searchindex001' exists as part of the
            # 'ddoc001' design document in the remote database...
            # Retrieve documents where the Lucene field name is 'name' and
            # the value is 'julia*'
            resp = db.get_search_result('ddoc001', 'searchindex001',
                                        query='name:julia*',
                                        include_docs=True)
            for row in resp['rows']:
                # Process search index data (in JSON format).

        Example if the search query requires grouping by using
        the ``group_field`` parameter:

        .. code-block:: python

            # Assuming that 'searchindex001' exists as part of the
            # 'ddoc001' design document in the remote database...
            # Retrieve JSON response content, limiting response to 10 documents
            resp = db.get_search_result('ddoc001', 'searchindex001',
                                        query='name:julia*',
                                        group_field='name',
                                        limit=10)
            for group in resp['groups']:
                for row in group['rows']:
                # Process search index data (in JSON format).

        :param str ddoc_id: Design document id used to get the search result.
        :param str index_name: Name used in part to identify the index.
        :param str bookmark: Optional string that enables you to specify which
            page of results you require. Only valid for queries that do not
            specify the ``group_field`` query parameter.
        :param list counts: Optional JSON array of field names for which
            counts should be produced. The response will contain counts for each
            unique value of this field name among the documents matching the
            search query.
            Requires the index to have faceting enabled.
        :param list drilldown:  Optional list of fields that each define a
            pair of a field name and a value. This field can be used several
            times.  The search will only match documents that have the given
            value in the field name. It differs from using
            ``query=fieldname:value`` only in that the values are not analyzed.
        :param str group_field: Optional string field by which to group
            search matches.  Fields containing other data
            (numbers, objects, arrays) can not be used.
        :param int group_limit: Optional number with the maximum group count.
            This field can only be used if ``group_field`` query parameter
            is specified.
        :param group_sort: Optional JSON field that defines the order of the
            groups in a search using ``group_field``. The default sort order
            is relevance. This field can have the same values as the sort field,
            so single fields as well as arrays of fields are supported.
        :param int limit: Optional number to limit the maximum count of the
            returned documents. In case of a grouped search, this parameter
            limits the number of documents per group.
        :param query/q: A Lucene query in the form of ``name:value``.
            If name is omitted, the special value ``default`` is used.
            The ``query`` parameter can be abbreviated as ``q``.
        :param ranges: Optional JSON facet syntax that reuses the standard
            Lucene syntax to return counts of results which fit into each
            specified category. Inclusive range queries are denoted by brackets.
            Exclusive range queries are denoted by curly brackets.
            For example ``ranges={"price":{"cheap":"[0 TO 100]"}}`` has an
            inclusive range of 0 to 100.
            Requires the index to have faceting enabled.
        :param sort: Optional JSON string of the form ``fieldname<type>`` for
            ascending or ``-fieldname<type>`` for descending sort order.
            Fieldname is the name of a string or number field and type is either
            number or string or a JSON array of such strings. The type part is
            optional and defaults to number.
        :param str stale: Optional string to allow the results from a stale
            index to be used. This makes the request return immediately, even
            if the index has not been completely built yet.
        :param list highlight_fields: Optional list of fields which should be
            highlighted.
        :param str highlight_pre_tag: Optional string inserted before the
            highlighted word in the highlights output.  Defaults to ``<em>``.
        :param str highlight_post_tag: Optional string inserted after the
            highlighted word in the highlights output.  Defaults to ``</em>``.
        :param int highlight_number: Optional number of fragments returned in
            highlights. If the search term occurs less often than the number of
            fragments specified, longer fragments are returned.  Default is 1.
        :param int highlight_size: Optional number of characters in each
            fragment for highlights.  Defaults to 100 characters.
        :param list include_fields: Optional list of field names to include in
            search results. Any fields included must have been indexed with the
            ``store:true`` option.

        :returns: Search query result data in JSON format
        """
        param_q = query_params.get('q')
        param_query = query_params.get('query')
        # Either q or query parameter is required
        if bool(param_q) == bool(param_query):
            raise CloudantArgumentError(
                'A single query/q parameter is required. '
                'Found: {0}'.format(query_params))

        # Validate query arguments and values
        for key, val in iteritems_(query_params):
            if key not in list(SEARCH_INDEX_ARGS.keys()):
                msg = 'Invalid argument: {0}'.format(key)
                raise CloudantArgumentError(msg)
            if not isinstance(val, SEARCH_INDEX_ARGS[key]):
                msg = (
                    'Argument {0} is not an instance of expected type: {1}'
                ).format(key, SEARCH_INDEX_ARGS[key])
                raise CloudantArgumentError(msg)
        # Execute query search
        headers = {'Content-Type': 'application/json'}
        ddoc = DesignDocument(self, ddoc_id)
        resp = self.r_session.post(
            '/'.join([ddoc.document_url, '_search', index_name]),
            headers=headers,
            data=json.dumps(query_params, cls=self.client.encoder)
        )
        resp.raise_for_status()
        return resp.json()
