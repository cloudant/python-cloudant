#!/usr/bin/env python
# Copyright (C) 2018 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Partitioned databases introduce the ability for a user to create logical groups
of documents called partitions by providing a partition key with each document.

.. warning:: Your Cloudant cluster must have the ``partitions`` feature enabled.
             A full list of enabled features can be retrieved by calling the
             client :meth:`~cloudant.client.CouchDB.metadata` method.

Creating a partitioned database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    db = client.create_database('mydb', partitioned=True)

Handling documents
^^^^^^^^^^^^^^^^^^

The document ID contains both the partition key and document key in the form
``<partitionkey>:<documentkey>`` where:

- Partition Key *(string)*. Must be non-empty. Must not contain colons (as this
  is the partition key delimiter) or begin with an underscore.
- Document Key *(string)*. Must be non-empty. Must not begin with an underscore.

Be aware that ``_design`` documents and ``_local`` documents must not contain a
partition key as they are global definitions.

**Create a document**

.. code-block:: python

    partition_key = 'Year2'
    document_key = 'julia30'

    db.create_document({
        '_id': ':'.join((partition_key, document_key)),
        'name': 'Jules',
        'age': 6
    })

**Get a document**

.. code-block:: python

    doc = db[':'.join((partition_key, document_key))]

    # OR...

    partition = db.get_partition(partition_key)
    doc = partition[document_key]

Creating design documents
^^^^^^^^^^^^^^^^^^^^^^^^^

To define partitioned indexes you must set the ``partitioned=True`` optional
when constructing the new ``DesignDocument`` class.

.. code-block:: python

    ddoc = DesignDocument(db, document_id='view', partitioned=True)
    ddoc.add_view('myview','function(doc) { emit(doc.foo, doc.bar); }')
    ddoc.save()

Similarly, to define a partitioned Cloudant Query index you must set the
``partitioned=True`` optional.

.. code-block:: python

    index = db.create_query_index(
        design_document_id='query',
        index_name='foo-index',
        fields=['foo'],
        partitioned=True
    )

    index.create()

Querying Data
^^^^^^^^^^^^^

A partition key can be specified when querying data so that results can be
constrained to a specific database partition.

.. warning:: To run partitioned queries the database itself must be partitioned.

**Query**

.. code-block:: python

    partition = db.get_partition(partition_key)
    for result in partition.query(selector={'name': {'$eq': 'Jules'}}, use_index='_design/query')):
        ...

See :meth:`~cloudant.database.CouchDatabase.get_query_result` for a full
list of supported parameters.

**Search**

.. code-block:: python

    partition = db.get_partition(partition_key)
    results = partition.search('_design/search', 'mysearch', q='name:Jules')

    for result in results['rows']:
       ...

See :meth:`~cloudant.database.CloudantDatabase.get_search_result` for a full
list of supported parameters.

**Views (MapReduce)**

.. code-block:: python

    partition = db.get_partition(partition_key)
    for result in partition.view('_design/view', 'myview')
       ...

See :meth:`~cloudant.database.CouchDatabase.get_view_result` for a full
list of supported parameters.
"""


class DatabasePartition(object):
    """
    Database partition.

    :param str partition_key: Partition key.
    """
    def __init__(self, db, partition_key):
        self._db = db
        self._partition_key = partition_key

    def __contains__(self, item):
        """
        Check if a document exists in this database partition.

        See :meth:`cloudant.database.CouchDatabase.__contains__`.

        :param str item: Document ID.
        :returns: ``True`` if the document exists in the database partition,
            otherwise ``False``.
        :rtype: bool
        """
        return self._db.__contains__(self._get_doc_id(item))

    def __getitem__(self, key):
        """
        Get a document instance for the specified key from this database
        partition.

        See :meth:`cloudant.database.CouchDatabase.__getitem__`.

        :param str key: Document ID used to retrieve the document from the
            database.
        :returns: A Document or DesignDocument object depending on the specified
            document ID (key).
        :rtype: :class:`~cloudant.document.Document`,
            :class:`~cloudant.design_document.DesignDocument`
        """
        return self._db.__getitem__(self._get_doc_id(key))

    def _get_doc_id(self, doc_key):
        """
        Get document ID.
        """
        return '{partition_key}:{doc_key}'.format(
            partition_key=self._partition_key,
            doc_key=doc_key
        )

    @property
    def partition_key(self):
        """
        Get partition key.

        :return: Partition key.
        :rtype: str
        """
        return self._partition_key

    def query(self, *args, **kwargs):
        """
        Run a query over this database partition.

        See :meth:`~cloudant.database.CouchDatabase.get_query_result` for a full
        list of supported parameters.

        :return: The result.
        """
        return self._db.get_query_result(*args,
                                         partition_key=self._partition_key,
                                         **kwargs)

    def search(self, *args, **kwargs):
        """
        Run a search over this database partition.

        See :meth:`~cloudant.database.CloudantDatabase.get_search_result` for a
        full list of supported parameters.

        :return: The result.
        """
        return self._db.get_search_result(*args,
                                          partition_key=self._partition_key,
                                          **kwargs)

    def view(self, *args, **kwargs):
        """
        Run a view over this database partition.

        See :meth:`~cloudant.database.CouchDatabase.get_view_result` for a full
        list of supported parameters.

        :return: The result.
        """
        return self._db.get_view_result(*args,
                                        partition_key=self._partition_key,
                                        **kwargs)
