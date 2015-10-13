Cloudant Python Client
======================

.. image:: https://magnum.travis-ci.com/cloudant/python-cloudant.svg?token=YYmxubNGds1Kt16kQ9v7&branch=master
   :target: https://magnum.travis-ci.com/cloudant/python-cloudant

This library is currently a preview (alpha version) of Cloudant's new official 
Python library.  As such it currently does not have complete API coverage nor is the
documentation 100% complete.  We are busily working towards bridging the API and 
documentation gaps, so please check back often as additions/changes will be 
occuring frequently.

.. contents::
    :local:
    :depth: 2
    :backlinks: none

======================
Installation and Usage
======================

Released versions of this library are `hosted on PyPI <https://pypi.python.org/pypi/cloudant>`_ 
and can be installed with ``pip``. 

The latest stable version on PyPI is 0.5.9, **but is now deprecated**. 

The current development version, which you should now use, is 2.0.0a1. Version 2.x makes
significant breaking changes -- no attempt was made to reproduce the API of 0.5.9.

Because 2.0.0 is still in development (2.0.0a1) and we wish to give developers time to 
upgrade, version 0.5.9 will remain the latest stable version on PyPI until at least early
2016.  

In order to install version 2.0.0a1 or greater, execute

.. code-block:: bash

    pip install --pre cloudant

In order to install the deprecated 0.5.9, execute

.. code-block:: bash

    pip install cloudant

===============
Getting started
===============

Now it's time to begin doing some work with Cloudant and Python.  For working
code samples of any of the API's please go to our test suite.

***********
Connections
***********

In order to manage a connection you must first initialize the connection by 
constructing either a ``Cloudant`` or ``CouchDB`` client.  Since connecting to 
the Cloudant managed service provides extra end points as compared to a CouchDB 
instance, we provide the two different client implementations in order to 
connect to the desired database service.  Once the client is constructed, 
you follow that up by connecting to the account, performing your tasks, and then 
disconnecting from the account.

Later in the `Context managers`_ section we will see how to 
simplify this process through the use of the Python *with* statement.

Connecting with a client
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Use CouchDB to create a CouchDB client
    # from cloudant.account import CouchDB
    # client = CouchDB(USERNAME, PASSWORD, url='http://127.0.0.1:5984')

    # Use Cloudant to create a Cloudant client using account
    from cloudant.account import Cloudant
    client = Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME)
    # or using url
    # client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com')
    
    # Connect to the account
    client.connect()

    # Perform client tasks...
    session = client.session()
    print 'Username: {0}'.format(session['userCtx']['name'])
    print 'Databases: {0}'.format(client.all_dbs())

    # Disconnect from the account
    client.disconnect()

*********
Databases
*********

Once a connection is established you can then create a database, open an 
existing database, or delete a database.  The following examples assume a client 
connection has already been established.

Creating a database
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Create a database using an initialized client
    # The result is a new CloudantDatabase or CouchDatabase based on the client
    my_database = client.create_database('my_database')

    # You can check that the database exists
    if my_database.exists():
        print 'SUCCESS!!'

Opening a database
^^^^^^^^^^^^^^^^^^

Opening an existing database is done by supplying the name of an existing 
database to the client.  Since the ``Cloudant`` and ``CouchDB`` classes are 
sub-classes of ``dict``, this is accomplished through standard ``dict`` 
notation.

.. code-block:: python

    # Open an existing database
    my_database = client['my_database']

Deleting a database
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Delete a database using an initialized client
    client.delete_database('my_database')

*********
Documents
*********

Working with documents using this library is handled through the use of 
Document objects and Database API methods.  A document context 
manager is also provided to simplify the process.  This is discussed later in 
the `Context managers`_ section.  The examples that follow demonstrate how to 
create, read, update, and delete a document.  These examples assume that 
either a CloudantDatabase or a CouchDatabase object already exists.

Creating a document
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Create document content data
    data = {
        '_id': 'julia30', # Setting _id is optional
        'name': 'Julia',
        'age': 30,
        'pets': ['cat', 'dog', 'frog']
        }

    # Create a document using the Database API
    my_document = my_database.create_document(data)

    # Check that the document exists in the database
    if my_document.exists():
        print 'SUCCESS!!'

Retrieving a document
^^^^^^^^^^^^^^^^^^^^^

Accessing a document from a database is done by supplying the document 
identifier of an existing document to either a ``CloudantDatabase`` or a 
``CouchDatabase`` object.  Since the ``CloudantDatabase`` and ``CouchDatabase`` 
classes are sub-classes of ``dict``, this is accomplished through standard 
``dict`` notation.

.. code-block:: python

    my_document = my_database['julia30']

    # Display the document
    print my_document

Retrieve all documents
^^^^^^^^^^^^^^^^^^^^^^

You can also iterate over a ``CloudantDatabase`` or a ``CouchDatabase`` object 
to retrieve all documents in a database.

.. code-block:: python

    # Get all of the documents from my_database
    for document in my_database:
        print document

Update a document
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from cloudant.document import Document

    # First retrieve the document
    my_document = my_database['julia30']

    # Update the document content
    # This can be done as you would any other dictionary
    my_document['name'] = 'Jules'
    my_document['age'] = 6

    # You must save the document in order to update it on the database
    my_document.save()

Delete a document
^^^^^^^^^^^^^^^^^

.. code-block:: python

    # First retrieve the document
    my_document = my_database['julia30']

    # Delete the document
    my_document.delete()

********************
Dealing with results
********************

If you want to get Pythonic with your returned data content, we've added a 
``Result`` class that wraps your content and exposes Pythonic ways to access it. 
Instantiate a ``Result`` with a raw data callable such as ``all_docs`` from a 
database object or the callable reference from a ``view`` and then access the 
data as you would normally.  The following example uses ``all_docs`` and shows 
ways to slice and iterate over the result set.  It assumes that either a 
``CloudantDatabase`` or a ``CouchDatabase`` object already exists.

.. code-block:: python

    from cloudant.result import Result

    # Retrieve Result wrapped document content
    # The include_docs argument is optional and defaults to False
    result_set = Result(my_database.all_docs, include_docs=True)

    # Get the result for matching a key
    result = result_set['julia30']

    # Slice by startkey and endkey
    result = result_set['julia30':'ruby99'] # result between keys
    result = result_set['julia30':] # result after key
    result = result_set[:'ruby99'] # result up to key

    # Slice by block
    result = result_set[100:200] # result 100 to 200
    result = result_set[:200] # result up to the 200th
    result = result_set[100:] # result after the 100th

    # Iterate over results
    for result in result_set:
        print result

****************
Context managers
****************

Now that we've gone through the basics, let's take a look at how to simplify 
the process of connection, database acquisition, and document management 
through the use of Python *with* blocks and this library's context managers.  
Handling your business using *with* blocks saves you from having to connect and 
disconnect your client as well as saves you from having to perform a lot of 
fetch and save operations as the context managers handle these operations for 
you.  This example uses the ``cloudant`` context helper to illustrate the 
process but identical functionality exists for CouchDB through the use of the 
``couchdb`` context helper.

.. code-block:: python

    # cloudant context helper
    from cloudant import cloudant

    # couchdb context helper
    # from cloudant import couchdb

    from cloudant.document import Document

    # Perform a connect upon entry and a disconnect upon exit of the block
    with cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME) as client:
    
        # Perform client tasks...
        session = client.session()
        print 'Username: {0}'.format(session['userCtx']['name'])
        print 'Databases: {0}'.format(client.all_dbs())

        # Create a database
        my_database = client.create_database('my_database')
        if my_database.exists():
            print 'SUCCESS!!'

        # You can open an existing database
        del my_database
        my_database = client['my_database']
    
        # Performs a fetch upon entry and a save upon exit of this block
        # Use this context manager to create or update a Document
        with Document(my_database, 'julia30') as doc:
            doc['name'] = 'Julia'
            doc['age'] = 30
            doc['pets'] = ['cat', 'dog', 'frog']

        # Display a Document
        print my_database['julia30']
    
        # Delete the database
        client.delete_database('my_database')

        print 'Databases: {0}'.format(client.all_dbs())

****************
End point access
****************

This library is currently a preview of Cloudant's new Python library. As such 
it's currently not got complete API coverage. While we work towards this, API 
which isn't covered can still benefit from the client's authentication and 
session usage by directly accessing the underlying Requests_ session object. 
This can be used to access things like Cloudant Search and Cloudant Query while 
we finish off the API in the library.

Access the session object using the ``r_session`` attribute on your client 
object. From there, use the session to make requests as the user the client is 
set up with. The following example shows a ``GET`` to ``_all_docs``, but 
obviously you can use this for any HTTP request to the Cloudant/CouchDB server.  
This example assumes that either a ``Cloudant`` or a ``CouchDB`` client object 
already exists.

.. _Requests: http://docs.python-requests.org/en/latest/

.. code-block:: python

    # Define the end point and parameters
    end_point = '{0}/{1}'.format(client.cloudant_url, 'my_database/_all_docs')
    params = {'include_docs': 'true'}

    # Issue the request
    response = client.r_session.get(end_point, params=params)

    # Display the response content
    print response.json()

=============
API Reference
=============

Content coming soon...

===========
Development
===========

See `CONTRIBUTING.rst <https://github.com/cloudant/python-cloudant/blob/master/CONTRIBUTING.rst>`_

**********
Test Suite
**********

Content coming soon...

***********************
Using in other projects
***********************

Content coming soon...

*******
License
*******

Copyright © 2015 IBM. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
