#!/usr/bin/env python
# Copyright (c) 2015 IBM. All rights reserved.
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
_setup.py_

Cloudant / CouchDB Client Library

"""

from setuptools import setup, find_packages

requirements_file = open('requirements.txt')
requirements = requirements_file.read().strip().split('\n')
requirements_file.close()
version_file = open('VERSION')
version = version_file.read().strip()
version_file.close()

setup_args = {
    'description': 'Cloudant / CouchDB Client Library',
    'include_package_data': True,
    'install_requires': requirements,
    'name': 'cloudant',
    'version': version,
    'author': 'IBM',
    'author_email': 'alfinkel@us.ibm.com',
    'url': 'https://github.com/cloudant/python-cloudant',
    'packages': find_packages('./src'),
    'provides': find_packages('./src'),
    'package_dir': {'': 'src'},
    'classifiers': [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Software Development :: Libraries',
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5'
      ]
}

setup(**setup_args)
