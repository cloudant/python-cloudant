Developing this library
=======================

Python-Cloudant Client Library is written in Python.

=============================
Contributor License Agreement
=============================

In order for us to accept pull-requests, the contributor must first complete
a Contributor License Agreement (CLA). This clarifies the intellectual
property license granted with any contribution. It is for your protection as a
Contributor as well as the protection of IBM and its customers; it does not
change your rights to use your own Contributions for any other purpose.

This is a quick process: one option is signing using Preview on a Mac,
then sending a copy to us via email.

You can download the CLAs here:

- `Individual <http://cloudant.github.io/cloudant-sync-eap/cla/cla-individual.pdf>`_
- `Corporate <http://cloudant.github.io/cloudant-sync-eap/cla/cla-corporate.pdf>`_

If you are an IBMer, please contact us directly as the contribution process is
slightly different.

======================
Development Quickstart
======================

Clone the repo into a folder, set up a `virtual environment <https://virtualenv.pypa.io/en/latest/>`_, 
install the requirements, run the tests:

.. code-block:: bash

    $ git clone git clone git@github.com:cloudant/python-cloudant.git
    $ cd python-cloudant
    $ virtualenv .
    $ ./bin/activate
    $ pip install -r requirements.txt
    $ pip install -r test-requirements.txt
    $ nosetests -w ./tests/unit

At this point most of the tests will fail; I'm not sure why.
