#!/usr/bin/env python
"""
_database_

API class representing a cloudant database

"""
import json
import contextlib
import posixpath
import urllib

from .document import CloudantDocument
from .views import DesignDocument
from .errors import CloudantException
from .index import python_to_couch, Index
from .changes import Feed


class CloudantDatabase(dict):
    """
    _CloudantDatabase_

    """
    def __init__(self, cloudant, database_name, fetch_limit=100):
        super(CloudantDatabase, self).__init__()
        self._cloudant_account = cloudant
        self._database_host = cloudant._cloudant_url
        self._database_name = database_name
        self._r_session = cloudant._r_session
        self._fetch_limit = fetch_limit
        self.index = Index(self.all_docs)

    @property
    def database_url(self):
        return posixpath.join(
            self._database_host,
            urllib.quote_plus(self._database_name)
        )

    @property
    def security_url(self):
        parts = ['_api', 'v2', 'db', self._database_name,'_security']
        url = posixpath.join(self._database_host, *parts)
        return url

    @property
    def creds(self):
        """
        _creds_

        Return a dict of useful strings to use to authenicate against
        this database, using various methods.

        """
        return {
            "basic_auth": self._cloudant_account.basic_auth_str(),
            "user_ctx": self._cloudant_account.session()['userCtx']
        }

    def exists(self):
        resp = self._r_session.get(self.database_url)
        return resp.status_code == 200

    def metadata(self):
        resp = self._r_session.get(self.database_url)
        resp.raise_for_status()
        return resp.json()

    def doc_count(self):
        return self._metadata().get('doc_count')

    def create_document(self, data, throw_on_exists=False):
        doc = CloudantDocument(self, data.get('_id'))
        doc.update(data)
        doc.create()
        super(CloudantDatabase, self).__setitem__(doc['_id'], doc)
        return doc

    def new_document(self):
        """
        _new_document_

        Creates new, empty document
        """
        doc = CloudantDocument(self, None)
        doc.create()
        super(CloudantDatabase, self).__setitem__(doc['_id'], doc)
        return doc

    def design_documents(self):
        """
        _design_documents_

        Return the raw JSON content of the design documents for this database

        """
        url = posixpath.join(self.database_url, '_all_docs')
        query = "startkey=\"_design\"&endkey=\"_design0\"&include_docs=true"
        resp = self._r_session.get(url, params=query)
        resp.raise_for_status()
        data = resp.json()
        return data['rows']

    def list_design_documents(self):
        """
        _list_design_documents_

        Return a list of design document names on this database

        """
        url = posixpath.join(self.database_url, '_all_docs')
        query = "startkey=\"_design\"&endkey=\"_design0\""
        resp = self._r_session.get(url, params=query)
        resp.raise_for_status()
        data = resp.json()
        return [x.get('key') for x in data.get('rows', [])]

    def create(self):
        """
        _create_

        Create this database if it doesnt exist
        """
        if self.exists():
            return self

        resp = self._r_session.put(self.database_url)
        if resp.status_code == 201:
            return self

        raise CloudantException(
            u"Unable to create database {0}: Reason:{1}".format(
                self.database_url, resp.text
            ),
            code=resp.status_code
        )

    def delete(self):
        """
        _delete_

        Delete this database

        """
        resp = self._r_session.delete(self.database_url)
        resp.raise_for_status()

    def all_docs(self, **kwargs):
        """
        _all_docs_

        Wraps the _all_docs primary index on the database,
        and returns the results by value. This can be used
        as a direct query to the couch db all_docs endpoint.
        More convienient/efficient access using slices
        and iterators can be accessed via the index attribute

        Keyword arguments supported are those of the couch
        view/index access API.

        :param descending: Boolean. Return the documents in descending by key
            order
        :param endkey: string/list Stop returning records when the specified
            key is reached
        :param include_docs: Boolean. Include the full content of the documents
            in the return
        :param inclusive_end: Boolean. Include rows whose key equals the endkey
            boolean
        :param key: string. Return only documents that match the
            specified key
        :param limit: int. Limit the number of the returned documents
            to the specified number
        :param skip: int. Skip this number of records before starting to
           return the results
        :param startkey: str/list. Start returning records when the specified
          key matches this value

        :returns: Raw data JSON response from the all_docs endpoint containing
          rows, counts etc.

        """
        params = python_to_couch(kwargs)
        resp = self._r_session.get(
            posixpath.join(
                self.database_url,
                '_all_docs'
            ),
            params=params
        )
        data = resp.json()
        return data

    @contextlib.contextmanager
    def custom_index(self, **options):
        """
        _custom_index_

        If you want to customise the index behaviour on all_docs
        you can build your own with extra options to the index
        call using this context manager.

        Example:

        with view.custom_index(include_docs=True, reduce=False) as indx:
            data = indx[100:200]

        """
        indx = Index(self.all_docs, **options)
        yield indx
        del indx

    def keys(self, remote=False):
        """
        _keys_

        """
        if not remote:
            return super(CloudantDatabase, self).keys()
        docs = self.all_docs()
        return [row['id'] for row in docs.get('rows', [])]

    def changes(self, since=None, continuous=True, include_docs=False):
        """
        Implement streaming from changes feed. Yields any changes that occur.

        @param str since: Start from this sequence
        @param boolean continuous: Stream results?
        """
        changes_feed = Feed(
            self._r_session,
            posixpath.join(self.database_url, '_changes'),
            since=since,
            continuous=continuous,
            include_docs=include_docs
        )

        for change in changes_feed:
            if change:
                yield change

    def __getitem__(self, key):
        if key in self.keys():
            return super(CloudantDatabase, self).__getitem__(key)
        if key.startswith('_design/'):
            doc = DesignDocument(self, key)
        else:
            doc = CloudantDocument(self, key)
        if doc.exists():
            doc.fetch()
            super(CloudantDatabase, self).__setitem__(key, doc)
            return doc
        else:
            raise KeyError(key)

    def __iter__(self, remote=True):
        """
        ___iter___ wrapper around dict.__iter__

        By default, fetch docs from couch, in batches equal to
        self._fetch_limit, yielding results as we get them.

        Otherwise, pass through to built-in __iter__.

        @param boolean remote: Governs default behavior of freshly
            fetching docs from couch (if True), or just digging through
            locally cached docs (if False)

        """
        if not remote:
            super(CloudantDatabase, self).__iter__()
        else:
            next_startkey = 0
            while next_startkey is not None:
                docs = self.all_docs(
                    limit=self._fetch_limit + 1,  # Get one extra doc
                                                  # to use as
                                                  # next_startkey
                    include_docs="true",
                    startkey=json.dumps(next_startkey)
                ).get('rows', [])

                if len(docs) > self._fetch_limit:
                    next_startkey = docs.pop()['id']
                else:
                    # This is the last batch of docs, so we set
                    # ourselves up to break out of the while loop
                    # after this pass.
                    next_startkey = None

                for doc in docs:
                    super(CloudantDatabase, self).__setitem__(
                        doc['id'],
                        doc['doc']
                    )
                    yield doc

            raise StopIteration

    def security_document(self):
        """
        _security_document_

        Fetch the security document for this database
        which contains information about who the database
        is shared with

        GET _api/v2/db/<dbname>/_security

        """
        resp = self._r_session.get(self.security_url)
        resp.raise_for_status()
        return resp.json()

    def share_database(self, username, reader=True, writer=False, admin=False):
        """
        _share_database_

        Share this database with the username provided.
        You can grant varying degrees of access rights,
        default is to share read-only, but writing or admin
        permissions can be added by setting the appropriate flags
        If the user already has this database shared with them it
        will modify/overwrite the existing permissions

        :param username: Cloudant Username to share the database with
        :param reader: Grant named user read access if true
        :param writer: Grant named user write access if true
        :param admin: Grant named user admin access if true

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
        resp = self._r_session.put(
            self.security_url,
            data=json.dumps(doc),
            headers={'Content-Type': 'application/json'}
            )
        resp.raise_for_status()
        return resp.json()

    def unshare_database(self, username):
        """
        _unshare_database_

        Remove all sharing with the named user for this database.
        This will remove the entry for the user from the security doc
        To modify permissions, instead of remove thame,
        use the share_database method

        """
        doc = self.security_document()
        data = doc.get('cloudant', {})
        if username in data:
            del data[username]
        doc['cloudant'] = data
        resp = self._r_session.put(
            self.security_url,
            data=json.dumps(doc),
            headers={'Content-Type': 'application/json'}
            )
        resp.raise_for_status()
        return resp.json()

    def bulk_docs(self, *keys):
        """
        _bulk_docs_

        Retrieve documents for given list of keys via bulk doc API
        POST    /db/_all_docs   Returns certain rows from the built-in view of all documents

        """
        pass

    def bulk_insert(self, *docs):
        """
        _bulk_insert_

        POST multiple docs for insert, each doc must be a dict containing
        _id and _rev

        POST    /db/_bulk_docs  Insert multiple documents in to the database in a single request

        """
        pass

    def db_updates(self):
        """
        GET /_db_updates    Returns information about databases that have been updated

        """
        pass

    def shards(self):
        """
        GET /db/_shards Returns information about the shards in a database or the shard a document belongs to

        """
        pass

    def missing_revisions(self):
        """
        POST    /db/_missing_revs   Given a list of document revisions, returns the document revisions that do not exist in the database

        """
        pass

    def revisions_diff(self, *revisions):
        """
        POST    /db/_revs_diff  Given a list of document revisions, returns differences between the given revisions and ones that are in the database

        """
        pass

    def get_revision_limit(self, doc):
        """
        GET /db/_revs_limit Gets the limit of historical revisions to store for a single document in the database

        """
        pass

    def set_revision_limit(self, doc, limit):
        """
        PUT /db/_revs_limit Sets the limit of historical revisions to store for a single document in the database

        """
        pass

    def view_cleanup(self):
        """
        POST    /db/_view_cleanup   Removes view files that are not used by any design document

        """
        pass
