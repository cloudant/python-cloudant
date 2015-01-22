#!/usr/bin/env python
"""
_database_

API class representing a cloudant database

"""
import json
import posixpath
import urllib
import requests
from collections import Sequence

from .document import CloudantDocument
from .views import DesignDocument
from .errors import CloudantException
from .utils import python_to_couch, ALL_ARGS



class PrimaryIndex(object):
    """
    _PrimaryIndex_

    Slice/dict like access helper to the _all_docs endpoint
    for a given database

    """
    def __init__(self, database):
        self._database = database
        self._r_session = database._r_session

    def __getitem__(self, key):
        if isinstance(key, basestring):
            data = self._database.all_docs(key=key)
            return data['rows']

        if isinstance(key, Sequence):
            data = self._database.all_docs(key=key)
            return data['rows']

        if isinstance(key, slice):
            str_or_none_start = isinstance(key.start, (basestring, list)) or key.start is None
            str_or_none_stop =  isinstance(key.stop, (basestring, list)) or key.stop is None
            if str_or_none_start and str_or_none_stop:
                # startkey/endkey
                if key.stop is None and key.start is not None:
                    data = self._database.all_docs(startkey=key.start)
                if key.start is None and key.stop is not None:
                    data = self._database.all_docs(endkey=key.stop)
                if key.start is None and key.stop is None:
                    data = self._database.all_docs()
                if key.start is not None and key.stop is not None:
                    data = self._database.all_docs(startkey=key.start, endkey=key.stop)
                return data['rows']
            int_or_none_start = isinstance(key.start, (int)) or key.start is None
            int_or_none_stop = isinstance(key.stop, (int)) or key.stop is None
            if int_or_none_start and int_or_none_stop:
                if key.start is not None and key.stop is not None:
                    data = self._database.all_docs(skip=key.start, limit=key.stop)
                if key.start is not None and key.stop is None:
                    data = self._database.all_docs(skip=key.start)
                if key.start is None and key.stop is not None:
                    data = self._database.all_docs(limit=key.stop)
                if key.start is None and key.stop is None:
                    data = self._database.all_docs()
                data = self._database.all_docs(skip=key.start, limit=key.stop)
                return data['rows']

        raise RuntimeError("wtf is {0}?".format(key))


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
        self.index = PrimaryIndex(self)

    @property
    def database_url(self):
        return posixpath.join(
            self._database_host,
            urllib.quote_plus(self._database_name)
        )

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

        descending  Return the documents in descending by key order boolean false
        endkey  Stop returning records when the specified key is reached string
        include_docs    Include the full content of the documents in the return boolean false
        inclusive_end   Include rows whose key equals the endkey  boolean true
        key Return only documents that match the specified key  string
        limit   Limit the number of the returned documents to the specified number  numeric
        skip    Skip this number of records before starting to return the results  numeric 0
        startkey

        """
        for k in kwargs:
            if k not in ALL_ARGS:
                raise ValueError("Invalid argument: {0}".format(k))
        params = python_to_couch(kwargs)
        resp = self._r_session.get(posixpath.join(self.database_url, '_all_docs'), params=params)
        data = resp.json()
        return data

    def keys(self, remote=False):
        """
        _keys_

        """
        if not remote:
            return super(CloudantDatabase, self).keys()
        docs = self.all_docs()
        return [ row['id'] for row in docs.get('rows', []) ]

    def changes(self, since=None, continuous=True):
        """
        Implement streaming from changes feed.

        @param str since: Start from this sequence
        @param boolean continuous: Stream results?

        #TODO: this needs a whole lot of fleshing out. Writing enough
        to make some tests happy for now.

        """
        if not continuous:
            raise Exception(u"Non streaming changes not yet implemented!")

        stream = self._r_session.get(
            posixpath.join(
                self.database_url,
                '_changes',),
            params=dict(feed="continuous"),
            stream=True,
        )

        for chunk in stream.iter_lines(chunk_size=1):
            # Chunk size one theoretically kicks the last chunk out of
            # memory.
            if chunk.strip():
                yield json.loads(chunk)
        stream.close()

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
