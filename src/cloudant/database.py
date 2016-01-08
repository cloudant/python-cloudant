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
import urllib
from requests.exceptions import HTTPError

from .document import Document
from .design_document import DesignDocument
from .views import View
from .indexes import Index, SearchIndex, SpecialIndex
from .index_constants import JSON_INDEX_TYPE
from .index_constants import TEXT_INDEX_TYPE
from .index_constants import SPECIAL_INDEX_TYPE
from .query import Query
from .errors import CloudantException, CloudantArgumentError
from .result import python_to_couch, Result
from .changes import Feed

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
        self.cloudant_account = client
        self._database_host = client.cloudant_url
        self.database_name = database_name
        self.r_session = client.r_session
        self._fetch_limit = fetch_limit
        self.result = Result(self.all_docs)

    @property
    def database_url(self):
        """
        Constructs and returns the database URL.

        :returns: Database URL
        """
        return posixpath.join(
            self._database_host,
            urllib.quote_plus(self.database_name)
        )

    @property
    def creds(self):
        """
        Retrieves a dictionary of useful authentication information
        that can be used to authenticate against this database.

        :returns: Dictionary containing authentication information
        """
        return {
            "basic_auth": self.cloudant_account.basic_auth_str(),
            "user_ctx": self.cloudant_account.session()['userCtx']
        }

    def exists(self):
        """
        Performs an existence check on the remote database.

        :returns: Boolean True if the database exists, False otherwise
        """
        resp = self.r_session.get(self.database_url)
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
        the data provided, assuming that there is an _id field provided.

        :param dict data: Dictionary of document JSON data, containing _id.
        :param bool throw_on_exists: Optional flag dictating whether to raise
            an exception if the document already exists in the database.

        :returns: Document instance corresponding to the new document in the
            database
        """
        docid = data.get('_id')
        doc = Document(self, docid)
        if throw_on_exists:
            if doc.exists():
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

    def get_view_result(self, ddoc_id, view_name, **kwargs):
        """
        Retrieves a Result object based on the design document
        and view name.  If you intend to iterate through the
        result, do not use ``skip`` and/or ``limit`` in the kwargs as
        that is handled in the Result.  If you would like to
        manage paging and iteration manually over the result
        then use the
        :func:`~cloudant.database.CouchDatabase.get_view_raw_result`
        method instead.

        For example to retrieve the default Result object based on a
        design document view do:

        .. code-block:: python

            db.get_view_result('_design/ddoc_id_001', 'view_001')

        But to retrieve a customized Result object based on the
        same design document view do something like:

        .. code-block:: python

            db.get_view_result('_design/ddoc_id_001', 'view_001',
                include_docs=True, reduce=False)

        For more detail on slicing and iteration, refer to the
        :class:`~cloudant.result.Result` documentation.

        :param str ddoc_id: Design document id used to get result.
        :param str view_name: Name of the view used to get result.
        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are lists. Groups reduce results for the specified number
            of list fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int page_size: Sets the page size for result iteration.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: The result content wrapped in a Result object
        """
        view = View(DesignDocument(self, ddoc_id), view_name)
        if kwargs:
            return view.make_result(**kwargs)
        else:
            return view.result

    def get_view_raw_result(self, ddoc_id, view_name, **kwargs):
        """
        Retrieves the raw JSON content based on the design document
        and view name.  Unlike
        :func:`~cloudant.database.CouchDatabase.get_view_result` the use
        of ``skip`` and ``limit`` as kwargs is valid and
        actually necessary in order to manage paging and iteration.
        If you would like paging and iteration handled automatically for you
        then use the
        :func:`~cloudant.database.CouchDatabase.get_view_result`
        method instead.

        For example to retrieve the raw JSON response content based on a
        design document view do:

        .. code-block:: python

            db.get_view_raw_result('_design/ddoc_id_001', 'view_001')

        But to retrieve the raw JSON response content based on a set of
        parameters on the same design document view do something like:

        .. code-block:: python

            db.get_view_raw_result('_design/ddoc_id_001', 'view_001',
                include_docs=True, skip=100, limit=100, reduce=False)

        :param str ddoc_id: Design document id used to get result.
        :param str view_name: Name of the view used to get result.
        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool group: Using the reduce function, group the results to a
            group or single row.
        :param group_level: Only applicable if the view uses complex keys: keys
            that are lists. Groups reduce results for the specified number
            of list fields.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int limit: Limit the number of returned documents to the
            specified count.
        :param bool reduce: True to use the reduce function, false otherwise.
        :param int skip: Skip this number of rows from the start.
        :param str stale: Allow the results from a stale view to be used. This
            makes the request return immediately, even if the view has not been
            completely built yet. If this parameter is not given, a response is
            returned only after the view has been built.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: The raw JSON response content for the query requested
        """
        view = View(DesignDocument(self, ddoc_id), view_name)
        return view(**kwargs)

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
            u"Unable to create database {0}: Reason: {1}".format(
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
        Wraps the _all_docs primary index on the database,
        and returns the results by value. This can be used
        as a direct query to the _all_docs endpoint.
        More convenient/efficient access using slices
        and iterators can be accessed via the result attribute.

        Keyword arguments supported are those of the view/index access API.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int limit: Limit the number of returned documents to the
            specified count.
        :param int skip: Skip this number of rows from the start.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or, for complex keys, a ``list``.
        :param str startkey_docid: Return records starting with the specified
            document ID.

        :returns: Raw JSON response content from ``_all_docs`` endpoint

        """
        params = python_to_couch(kwargs)
        resp = self.r_session.get(
            posixpath.join(
                self.database_url,
                '_all_docs'
            ),
            params=params
        )
        data = resp.json()
        return data

    @contextlib.contextmanager
    def custom_result(self, **options):
        """
        Provides a context manager that can be used to customize the
        ``_all_docs`` behavior and wrap the output as a
        :class:`~cloudant.result.Result`.

        :param bool descending: Return documents in descending key order.
        :param endkey: Stop returning records at this specified key.  Can be
            either a ``str`` or ``list``.
        :param str endkey_docid: Stop returning records when the specified
            document id is reached.
        :param bool include_docs: Include the full content of the documents.
        :param bool inclusive_end: Include rows with the specified endkey.
        :param str key: Return only documents that match the specified key.
        :param list keys: Return only documents that match the specified keys.
        :param int page_size: Sets the page size for result iteration.
        :param startkey: Return records starting with the specified key.  Can be
            either a ``str`` or ``list``
        :param str startkey_docid: Return records starting with the specified
            document ID.

        For example:

        .. code-block:: python

            with database.custom_result(include_docs=True) as rslt:
                data = rslt[100:200]
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
            return super(CouchDatabase, self).keys()
        docs = self.all_docs()
        return [row['id'] for row in docs.get('rows', [])]

    def changes(self, since=None, continuous=True, include_docs=False):
        """
        Streams data from _changes feed. Yields information about
        changes that have been made.

        :param str since: Change streaming starts from this sequence identifier.
        :param bool continuous: Dictates the streaming of data.
            Defaults to True.

        :returns: Iterable stream of changes
        """
        changes_feed = Feed(
            self.r_session,
            posixpath.join(self.database_url, '_changes'),
            since=since,
            continuous=continuous,
            include_docs=include_docs
        )

        for change in changes_feed:
            if change:
                yield change

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
        if key in self.keys():
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
                    document = {}
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
            fetch_limit=100
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

    def share_database(self, username, reader=True, writer=False, admin=False):
        """
        Shares the current remote database with the username provided.
        You can grant varying degrees of access rights,
        default is to share read-only, but writing or admin
        permissions can be added by setting the appropriate flags
        If the user already has this database shared with them it
        will modify/overwrite the existing permissions.

        :param str username: Cloudant user to share the database with.
        :param bool reader: Grant named user read access if True.
        :param bool writer: Grant named user write access if True.
        :param bool admin: Grant named user admin access if True.

        :returns: Share database status in JSON format
        """
        doc = self.security_document()
        data = doc.get('cloudant', {})
        perms = []
        if reader:
            perms.append('_reader')
        if writer:
            perms.append('_writer')
        if admin:
            perms.append('_admin')

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

    def get_all_indexes(self, raw_result=False):
        """
        Retrieves indexes from the remote database.

        :param bool raw_result: If set to True then the raw JSON content for
            the request is returned.  Default is to return a list containing
            :class:`~cloudant.indexes.Index`,
            :class:`~cloudant.indexes.SearchIndex`, and
            :class:`~cloudant.indexes.SpecialIndex` wrapped objects.

        :returns: The indexes in the database
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
                indexes.append(SearchIndex(
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

    def create_index(
            self,
            design_document_id=None,
            index_name=None,
            index_type='json',
            **kwargs
    ):
        """
        Creates either a JSON or a text index in the remote database.

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
        index = None
        if index_type == JSON_INDEX_TYPE:
            index = Index(self, design_document_id, index_name, **kwargs)
        elif index_type == TEXT_INDEX_TYPE:
            index = SearchIndex(self, design_document_id, index_name, **kwargs)
        else:
            msg = (
                'Invalid index type: {0}.  '
                'Index type must be either \"json\" or \"text\"'
            ).format(index_type)
            raise CloudantArgumentError(msg)
        index.create()
        return index

    def delete_index(self, design_document_id, index_type, index_name):
        """
        Deletes the index identified by the design document id, index type and
        index name from the remote database.

        :param str design_document_id: The design document id that the index
            exists in.
        :param str index_type: The type of the index to be deleted.  Must
            be either 'text' or 'json'.
        :param str index_name: The index name of the index to be deleted.
        """
        index = None
        if index_type == JSON_INDEX_TYPE:
            index = Index(self, design_document_id, index_name)
        elif index_type == TEXT_INDEX_TYPE:
            index = SearchIndex(self, design_document_id, index_name)
        else:
            msg = (
                'Invalid index type: {0}.  '
                'Index type must be either \"json\" or \"text\"'
            ).format(index_type)
            raise CloudantArgumentError(msg)
        index.delete()

    def get_query_result(self, selector, fields=None, raw_result=False, **kwargs):
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
        query = Query(self, selector=selector, fields=fields)
        if raw_result:
            return query(**kwargs)
        if kwargs:
            return query.make_result(**kwargs)
        else:
            return query.result
