Cloudant Python Client
======================

|build-status| |docs|

.. |build-status| image:: https://travis-ci.org/cloudant/python-cloudant.png
    :alt: build status
    :scale: 100%
    :target: https://travis-ci.org/cloudant/python-cloudant

.. |docs| image:: https://readthedocs.org/projects/pip/badge/
    :alt: docs
    :scale: 100%
    :target: http://python-cloudant.readthedocs.org

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

The latest stable version on PyPI is 0.5.10, **but is now deprecated**. 

The current development version, which you should now use, is 2.0.0a2. Version 2.x makes
significant breaking changes -- no attempt was made to reproduce the API of 0.5.10.

Because 2.0.0 is still in development (2.0.0a2) and we wish to give developers time to 
upgrade, version 0.5.10 will remain the latest stable version on PyPI until at least early
2016.  

In order to install version 2.0.0a1 or greater, execute

.. code-block:: bash

    pip install --pre cloudant

In order to install the deprecated 0.5.10, execute

.. code-block:: bash

    pip install cloudant

===============
Getting started
===============

See `Getting started (readthedocs.org) <http://python-cloudant.readthedocs.org/en/latest/getting_started.html>`_

=============
API Reference
=============

See `API reference docs (readthedocs.org) <http://python-cloudant.readthedocs.org/en/latest/cloudant.html>`_

=====================
Related Documentation
=====================

* `Cloudant Python client library docs (readthedocs.org) <http://python-cloudant.readthedocs.org>`_
* `Cloudant documentation <http://docs.cloudant.com/>`_
* `Cloudant for developers <https://cloudant.com/for-developers/>`_

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
