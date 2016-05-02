===============
Getting started
===============

Now it's time to begin doing some work with Cloudant and Python.  For working
code samples of any of the API's please go to our test suite.

.. toctree::
   :maxdepth: 2

***********
Connections
***********

In order to manage a connection you must first initialize the connection by 
constructing either a ``Cloudant`` or ``CouchDB`` client.  Since connecting to 
the Cloudant managed service provides extra end points as compared to a CouchDB 
server, we provide the two different client implementations in order to 
connect to the desired database service.  Once the client is constructed, 
you follow that up by connecting to the server, performing your tasks, and
then disconnecting from the server.

Later in the `Context managers`_ section we will see how to 
simplify this process through the use of the Python *with* statement.

Connecting with a client
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Use CouchDB to create a CouchDB client
    # from cloudant.client import CouchDB
    # client = CouchDB(USERNAME, PASSWORD, url='http://127.0.0.1:5984')

    # Use Cloudant to create a Cloudant client using account
    from cloudant.client import Cloudant
    client = Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME)
    # or using url
    # client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com')
    
    # Connect to the server
    client.connect()

    # Perform client tasks...
    session = client.session()
    print 'Username: {0}'.format(session['userCtx']['name'])
    print 'Databases: {0}'.format(client.all_dbs())

    # Disconnect from the server
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
sub-classes of ``dict``, this can be accomplished through standard Python
``dict`` notation.

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
``Result`` class that provides a key accessible, sliceable, and iterable 
interface to result collections.  To use it, construct a ``Result`` object 
passing in a reference to a raw data callable such as the ``all_docs`` method 
from a database object or a ``view`` object itself, which happens to be defined 
as callable and then access the data as you would using standard Python key 
access, slicing, and iteration techniques.  The following set of examples 
illustrate ``Result`` key access, slicing and iteration over a result collection 
in action.  It assumes that either a ``CloudantDatabase`` or a ``CouchDatabase`` 
object already exists.

.. code-block:: python

    from cloudant.result import Result, ResultByKey

    # Retrieve Result wrapped document content.
    # Note: The include_docs parameter is optional and is used to illustrate that view query 
    # parameters can be used to customize the result collection.
    result_collection = Result(my_database.all_docs, include_docs=True)

    # Get the result at a given location in the result collection
    # Note: Valid result collection indexing starts at 0
    result = result_collection[0]                   # result is the 1st in the collection
    result = result_collection[9]                   # result is the 10th in the collection

    # Get the result for matching a key
    result = result_collection['julia30']           # result is all that match key 'julia30'
    
    # If your key is an integer then use the ResultByKey class to differentiate your integer 
    # key from an indexed location within the result collection which is also an integer.
    result = result_collection[ResultByKey(9)]      # result is all that match key 9

    # Slice by key values
    result = result_collection['julia30': 'ruby99'] # result is between and including keys
    result = result_collection['julia30': ]         # result is after and including key
    result = result_collection[: 'ruby99']          # result is up to and including key

    # Slice by index values
    result = result_collection[100: 200]            # result is between 100 to 200, including 200th
    result = result_collection[: 200]               # result is up to and including the 200th
    result = result_collection[100: ]               # result is after the 100th

    # Iterate over the result collection
    for result in result_collection:
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
process but identical functionality exists for CouchDB through the ``couchdb`` 
and ``couchdb_admin_party`` context helpers.

.. code-block:: python

    # cloudant context helper
    from cloudant import cloudant

    # couchdb context helper
    # from cloudant import couchdb

    from cloudant.document import Document

    # Perform a connect upon entry and a disconnect upon exit of the block
    with cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME) as client:

    # CouchDB variant
    # with couchdb(USERNAME, PASSWORD, url=COUCHDB_URL) as client:
    
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
Endpoint access
****************

If for some reason you need to call a Cloudant/CouchDB endpoint directly rather 
using the API you can still benefit from the Cloudant/CouchDB client's 
authentication and session usage by directly accessing its underlying Requests_ 
session object.

Access the session object using the ``r_session`` attribute on your client 
object. From there, use the session to make requests as the user the client is 
set up with. The following example shows a ``GET`` to the ``_all_docs`` 
endpoint, but obviously you can use this for any HTTP request to the 
Cloudant/CouchDB server.  This example assumes that either a ``Cloudant`` or a 
``CouchDB`` client object already exists.

.. _Requests: http://docs.python-requests.org/en/latest/

.. code-block:: python

    # Define the end point and parameters
    end_point = '{0}/{1}'.format(client.cloudant_url, 'my_database/_all_docs')
    params = {'include_docs': 'true'}

    # Issue the request
    response = client.r_session.get(end_point, params=params)

    # Display the response content
    print response.json()
