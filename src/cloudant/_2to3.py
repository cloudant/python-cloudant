# Copyright (c) 2016 IBM. All rights reserved.
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
Python 2 to 3 compatibility methods

The philosophy employed here is to treat py2 as the special case vs. py3 as
future Python releases presumably will retain new semamtics in py3.
"""
import sys

PY2 = sys.version_info[0] < 3
ENCODING = 'utf-8'
NONETYPE = type(None)

# pylint: disable=undefined-variable
STRTYPE = basestring if PY2 else str

# pylint: disable=undefined-variable
UNITYPE = unicode if PY2 else str


if PY2:
    # pylint: disable=wrong-import-position,no-name-in-module,import-error,unused-import
    from urllib import quote as url_quote, quote_plus as url_quote_plus
    from ConfigParser import RawConfigParser

    def iteritems_(adict):
        """
        iterate dict key, value tuples in a py2 and 3 compatible way

        :param dict adict:
        :return: iterator of (key, value) tuples
        """
        return adict.iteritems()

    def next_(itr):
        """
        return next item from an iterable is a py2 and 3 compatible way

        :param Iterable itr:
        :return: the next item in itr
        """
        return itr.next()
else:
    from urllib.parse import quote as url_quote, quote_plus as url_quote_plus  # pylint: disable=wrong-import-position,no-name-in-module,import-error,ungrouped-imports
    from configparser import RawConfigParser  # pylint: disable=wrong-import-position,no-name-in-module,import-error

    def iteritems_(adict):
        """
        iterate dict key, value tuples in a py2 and 3 compatible way

        :param dict adict:
        :return: iterator of (key, value) tuples
        """
        return adict.items()

    def next_(itr):
        """
        return the next item in an iterable in a py2 and 3 compatible way

        :param Iterable itr:
        :return: the next item in itr
        """
        return next(itr)


def bytes_(astr):
    """
    return a bytes representation of astr in a py2 and 3 compatible way

    :param str astr:
    :return: bytes object
    """
    return astr.encode(ENCODING) if hasattr(astr, 'encode') else astr


def unicode_(astr):
    """
    return a unicode string representation of astr in a py2 and 3 compatible way

    :param bytes astr:
    :return: unicode string
    """
    return astr.decode(ENCODING) if hasattr(astr, 'decode') else astr
