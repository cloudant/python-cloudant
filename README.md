# :warning: NO LONGER MAINTAINED :warning:

**This library is end-of-life and no longer supported.**

This repository will not be updated. The repository will be kept available in read-only mode.

Please see the [Migration Guide](./MIGRATION.md) for advice
about migrating to our replacement library
[cloudant-python-sdk](https://github.com/IBM/cloudant-python-sdk).

For FAQs and additional information please refer to the
[Cloudant blog](https://blog.cloudant.com/2021/06/30/Cloudant-SDK-Transition.html).

# Cloudant Python Client

[![Build Status](https://travis-ci.org/cloudant/python-cloudant.svg?branch=master)](https://travis-ci.org/cloudant/python-cloudant)
[![Readthedocs](https://readthedocs.org/projects/pip/badge/)](http://python-cloudant.readthedocs.io)
[![Compatibility](https://img.shields.io/badge/python-3.5-blue.svg)](http://python-cloudant.readthedocs.io/en/latest/compatibility.html)
[![pypi](https://img.shields.io/pypi/v/cloudant.svg)](https://pypi.python.org/pypi/cloudant)

This is the official Cloudant library for Python.

* [Installation and Usage](#installation-and-usage)
* [Getting Started](#getting-started)
* [API Reference](http://python-cloudant.readthedocs.io/en/latest/cloudant.html)
* [Related Documentation](#related-documentation)
* [Development](#development)
    * [Contributing](CONTRIBUTING.md)
    * [Test Suite](CONTRIBUTING.md#running-the-tests)
    * [Using in Other Projects](#using-in-other-projects)
    * [License](#license)
    * [Issues](#issues)
* [Migrating to `cloudant-python-sdk` library](#migrating-to-cloudant-python-sdk-library)

## Installation and Usage


Released versions of this library are [hosted on PyPI](https://pypi.python.org/pypi/cloudant) and can be installed with `pip`.

In order to install the latest version, execute

    pip install cloudant

## Getting started

See [Getting started (readthedocs.io)](http://python-cloudant.readthedocs.io/en/latest/getting_started.html)

## API Reference

See [API reference docs (readthedocs.io)](http://python-cloudant.readthedocs.io/en/latest/cloudant.html)

## Related Documentation

* [Cloudant Python client library docs (readthedocs.io)](http://python-cloudant.readthedocs.io)
* [Cloudant documentation](https://console.bluemix.net/docs/services/Cloudant/cloudant.html#overview)
* [Cloudant Learning Center](https://developer.ibm.com/clouddataservices/cloudant-learning-center/)
* [Tutorial for creating and populating a database on IBM Cloud](https://console.bluemix.net/docs/services/Cloudant/tutorials/create_database.html#creating-and-populating-a-simple-cloudant-nosql-db-database-on-ibm-cloud)

## Development

See [CONTRIBUTING.md](https://github.com/cloudant/python-cloudant/blob/master/CONTRIBUTING.md)

## Using in other projects

The preferred approach for using `python-cloudant` in other projects is to use the PyPI as described above.

### Examples in open source projects

[Getting Started with Python Flask on IBM Cloud](https://github.com/IBM-Cloud/get-started-python)

[Movie Recommender Demo](https://github.com/snowch/movie-recommender-demo):
- [Update and check if documents exist](https://github.com/snowch/movie-recommender-demo/blob/master/web_app/app/dao.py#L162-L168)
- [Connect to Cloudant using 429 backoff with 10 retries](https://github.com/snowch/movie-recommender-demo/blob/master/web_app/app/cloudant_db.py#L17-L18)

[Watson Recipe Bot](https://github.com/ibm-watson-data-lab/watson-recipe-bot-python-cloudant):
- [Use Cloudant Query to find design docs](https://github.com/ibm-watson-data-lab/watson-recipe-bot-python-cloudant/blob/master/souschef/cloudant_recipe_store.py#L33-L77)

## License

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

## Issues

Before opening a new issue please consider the following:
* Only the latest release is supported. If at all possible please try to reproduce the issue using
the latest version.
* Please check the [existing issues](https://github.com/cloudant/python-cloudant/issues)
to see if the problem has already been reported. Note that the default search
includes only open issues, but it may already have been closed.
* Cloudant customers should contact Cloudant support for urgent issues.
* When opening a new issue [here in github](../../issues) please complete the template fully.

## Migrating to `cloudant-python-sdk` library
We have a newly supported Cloudant Python SDK named [cloudant-python-sdk](https://github.com/IBM/cloudant-python-sdk).
For advice on migrating from this module see [MIGRATION.md](MIGRATION.md).
