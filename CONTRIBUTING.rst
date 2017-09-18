Developing this library
=======================

Python-Cloudant Client Library is written in Python.

===============================
Developer Certificate of Origin
===============================

In order for us to accept pull-requests, the contributor must sign-off a
`Developer Certificate of Origin (DCO) <DCO1.1.txt>`_. This clarifies the
intellectual property license granted with any contribution. It is for your
protection as a Contributor as well as the protection of IBM and its customers;
it does not change your rights to use your own Contributions for any other
purpose.

Please read the agreement and acknowledge it by ticking the appropriate box in
the PR text, for example:

- [x] Tick to sign-off your agreement to the Developer Certificate of Origin (DCO) 1.1

======================
Development Quickstart
======================

Clone the repo into a folder, set up a `virtual environment <https://virtualenv.pypa.io/en/latest/>`_, 
install the requirements:

.. code-block:: bash

    $ git clone git clone git@github.com:cloudant/python-cloudant.git
    $ cd python-cloudant
    $ virtualenv .
    $ ./bin/activate
    $ pip install -r requirements.txt
    $ pip install -r test-requirements.txt
    
Before running the tests, start CouchDB:

.. code-block:: bash
    
    $ couchdb

The tests create databases in your CouchDB instance, these are `db-<uuid4()>`. 
They also create and delete documents in the `_replicator` database.

Now, run the tests. Here, I use the ``ADMIN_PARTY`` environment variable to
tell the tests not to use any authentication. See below for the full set of
variables that can be used.

.. code-block:: bash

    $ ADMIN_PARTY=true nosetests -w ./tests/unit
    
There are several environment variables which affect
test behaviour:

- ``RUN_CLOUDANT_TESTS``: set this to run the tests that use Cloudant-specific features. If
  you set this, you must set one of the following combinations of other variables:
    - ``DB_URL``, ``DB_USER`` and ``DB_PASSWORD``.
    - ``CLOUDANT_ACCOUNT``, ``DB_USER`` and ``DB_PASSWORD``.
    - If you set both ``DB_URL`` and ``CLOUDANT_ACCOUNT``, ``DB_URL`` is used as the
      URL to make requests to and ``CLOUDANT_ACCOUNT`` is inserted into the ``X-Cloudant-User``
      header.
- Without ``RUN_CLOUDANT_TESTS``, the following environment variables have an effect:
    - Set ``DB_URL`` to set the root URL of the CouchDB/Cloudant instance. It defaults
      to ``http://localhost:5984``.
    - Set ``ADMIN_PARTY`` to ``true`` to not use any authentication details.
    - Without ``ADMIN_PARTY``, set ``DB_USER`` and ``DB_PASSWORD`` to use those
      credentials to access the database.
    - Without ``ADMIN_PARTY`` and ``DB_USER``, the tests assume CouchDB is in
      admin party mode, but create a user via ``_config`` to run tests as.
      This user is deleted at the end of the test run, but beware it'll 
      break other applications using the CouchDB instance that rely on
      admin party mode being in effect while the tests are running.
