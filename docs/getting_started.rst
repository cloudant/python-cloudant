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

Note: If you require retrying requests after an HTTP 429 error, the
``Replay429Adapter`` can be added when constructing a ``Cloudant``
client and configured with an initial back off and retry count.

Note: Currently, the connect and read timeout will wait forever for
a HTTP connection or a response on all requests.  A timeout can be
set using the ``timeout`` argument when constructing a client.

Connecting with a client
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Use CouchDB to create a CouchDB client
    # from cloudant.client import CouchDB
    # client = CouchDB(USERNAME, PASSWORD, url='http://127.0.0.1:5984')

    # Use Cloudant to create a Cloudant client using account
    from cloudant.client import Cloudant
    client = Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME, connect=True)
    # or using url
    # client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com')

    # or with a 429 replay adapter that includes configured retries and initial backoff
    # client = Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME,
    #                   adapter=Replay429Adapter(retries=10, initialBackoff=0.01))

    # or with a connect and read timeout of 5 minutes
    # client = Cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME,
    #                   timeout=300)

    # Perform client tasks...
    session = client.session()
    print('Username: {0}'.format(session['userCtx']['name']))
    print('Databases: {0}'.format(client.all_dbs()))

    # Disconnect from the server
    client.disconnect()

**************
Authentication
**************

When constructing a ``Cloudant`` client, you can authenticate using the
`cookie authentication <http://guide.couchdb.org/editions/1/en/security.html#cookies>`_ functionality.
The server will always attempt to automatically renew the cookie
shortly before its expiry. However, if the client does not send a
request to the server during this renewal window and
``auto_renew=False`` then the cookie is not renewed.

Using ``auto_renew=True`` will attempt to renew the cookie at
any point during the lifetime of the session when either of the
following statements hold true:

- The server returns a ``credentials_expired`` error message.
- The server returns a ``401 Unauthorized`` status code.
- The server returns a ``403 Forbidden`` status code.

.. code-block:: python

    # Create client using auto_renew to automatically renew expired cookie auth
    client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com',
                     connect=True,
                     auto_renew=True)


************************************
Identity and Access Management (IAM)
************************************

IBM Cloud Identity & Access Management enables you to securely authenticate
users and control access to all cloud resources consistently in the IBM Bluemix
Cloud Platform.

See `IBM Cloud Identity and Access Management <https://console.bluemix.net/docs/services/Cloudant/guides/iam.html#ibm-cloud-identity-and-access-management>`_
for more information.

The production IAM token service at *https://iam.bluemix.net/identity/token* is used
by default. You can set an ``IAM_TOKEN_URL`` environment variable to override
this.

You can easily connect to your Cloudant account using an IAM API key:

.. code-block:: python

    # Authenticate using an IAM API key
    client = Cloudant.iam(ACCOUNT_NAME, API_KEY, connect=True)


****************
Resource sharing
****************

The ``Cloudant`` or ``CouchDB`` client objects make HTTP calls using the ``requests`` library.
``requests`` uses the `urllib3 <https://pypi.python.org/pypi/urllib3>`_ library which features
connection pooling and thread safety.

Connection pools can be managed by using the ``requests`` library's
`HTTPAdapter <https://github.com/kennethreitz/requests/blob/master/requests/adapters.py#L78>`_
when constructing a ``Cloudant`` or ``ClouchDB`` client instance.
The default number set by the ``urllib3`` library for cached connection pools is 10.
Use the ``HTTPAdapter`` argument ``pool_connections`` to set the number of
urllib3 connection pools to cache, and the ``pool_maxsize`` argument to set the
maximum number of connections to save in the pool.

Although the ``client`` session is documented as thread safe and it's possible for a
static ``client`` to be accessible by multiple threads, there are still cases that do not
guarantee thread safe execution.  It's recommended to use one ``client`` object per thread.

.. code-block:: python

    # Create client with 15 cached pool connections and a max pool size of 100
    httpAdapter = HTTPAdapter(pool_connections=15, pool_maxsize=100)
    client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com'
                     connect=True,
                     adapter=httpAdapter)

Note: Idle connections within the pool may be terminated by the server, so will not remain open
indefinitely meaning that this will not completely remove the overhead of creating new connections.

Using library in app server environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This library can be used in an app server, and the example
below shows how to use ``client`` in a ``flask`` app server.

.. code-block:: python

   from flask import Flask
   import atexit

   app = Flask(__name__)

   @app.route('/')
   def hello_world():
      # Cookie authentication can be renewed automatically using ``auto_renew=True``
      # which is typically what you would require when running in an application
      # server where the connection may stay open for a long period of time

      # Note: Each time you instantiate an instance of the Cloudant client, an
      # authentication request will be made to Cloudant to retrieve the session cookie.
      # If the performance overhead of this call is a concern for you, consider
      # using vanilla python requests with a custom subclass of HTTPAdapter that
      # performs the authentication call to Cloudant when it establishes the http
      # connection during the creation of the connection pool.
      client = Cloudant(USERNAME, PASSWORD, url='https://acct.cloudant.com',
                        connect=True,
                        auto_renew=True)

      # do something with client
      return 'Hello World!'

   # When shutting down the app server, use ``client.disconnect()`` to properly
   # logout and end the ``client`` session
   @atexit.register
   def shutdown():
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
        print('SUCCESS!!')

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
        print('SUCCESS!!')

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
    print(my_document)

Checking if a document exists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can check if a document exists in a database the same way you would check
if a ``dict`` has a key-value pair by key.

.. code-block:: python

    doc_exists = 'julia30' in my_database

    if doc_exists:
        print('document with _id julia30 exists')

Retrieve all documents
^^^^^^^^^^^^^^^^^^^^^^

You can also iterate over a ``CloudantDatabase`` or a ``CouchDatabase`` object 
to retrieve all documents in a database.

.. code-block:: python

    # Get all of the documents from my_database
    for document in my_database:
        print(document)

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
        print(result)

****************
Context managers
****************

Now that we've gone through the basics, let's take a look at how to simplify 
the process of connection, database acquisition, and document management 
through the use of Python *with* blocks and this library's context managers.  

Handling your business using *with* blocks saves you from having to connect and
disconnect your client as well as saves you from having to perform a lot of 
fetch and save operations as the context managers handle these operations for 
you.

This example uses the ``cloudant`` context helper to illustrate the
process but identical functionality exists for CouchDB through the ``couchdb`` 
and ``couchdb_admin_party`` context helpers.

.. code-block:: python

    from cloudant import cloudant

    # ...or use CouchDB variant
    # from cloudant import couchdb

    # Perform a connect upon entry and a disconnect upon exit of the block
    with cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME) as client:

    # ...or use CouchDB variant
    # with couchdb(USERNAME, PASSWORD, url=COUCHDB_URL) as client:
    
        # Perform client tasks...
        session = client.session()
        print('Username: {0}'.format(session['userCtx']['name']))
        print('Databases: {0}'.format(client.all_dbs()))

        # Create a database
        my_database = client.create_database('my_database')
        if my_database.exists():
            print('SUCCESS!!')

        # You can open an existing database
        del my_database
        my_database = client['my_database']

The following example uses the ``Document`` context manager. Here we make
multiple updates to a single document. Note that we don't save to the server
after each update. We only save once to the server upon exiting the ``Document``
context manager.

 .. code-block:: python

    from cloudant import cloudant
    from cloudant.document import Document

    with cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME) as client:

        my_database = client.create_database('my_database')

        # Upon entry into the document context, fetches the document from the
        # remote database, if it exists. Upon exit from the context, saves the
        # document to the remote database with changes made within the context
        # or creates a new document.
        with Document(database, 'julia006') as document:
            # If document exists, it's fetched from the remote database
            # Changes are made locally
            document['name'] = 'Julia'
            document['age'] = 6
            # The document is saved to the remote database

        # Display a Document
        print(my_database['julia30'])
    
        # Delete the database
        client.delete_database('my_database')

        print('Databases: {0}'.format(client.all_dbs()))

Always use the ``_deleted`` document property to delete a document from within
a ``Document`` context manager. For example:

 .. code-block:: python

    with Document(my_database, 'julia30') as doc:
        doc['_deleted'] = True

*You can also delete non underscore prefixed document keys to reduce the size of the request.*

.. warning:: Don't use the ``doc.delete()`` method inside your ``Document``
             context manager. This method immediately deletes the document on
             the server and clears the local document dictionary. A new, empty
             document is still saved to the server upon exiting the context
             manager.

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
    end_point = '{0}/{1}'.format(client.server_url, 'my_database/_all_docs')
    params = {'include_docs': 'true'}

    # Issue the request
    response = client.r_session.get(end_point, params=params)

    # Display the response content
    print(response.json())

***************
TLS 1.2 Support
***************

The TLS protocol is used to encrypt communications across a network to ensure
that transmitted data remains private. There are three released versions of TLS:
1.0, 1.1, and 1.2. All HTTPS connections use TLS.

If your server enforces the use of TLS 1.2 then the python-cloudant client will
continue to work as expected (assuming you're running a version of
Python/OpenSSL that supports TLS 1.2).
