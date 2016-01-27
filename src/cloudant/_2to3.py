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
python 2 to 3 compatibility methods
"""
import sys

PY2 = sys.version_info[0] < 3
ENCODING = 'utf-8'
NONETYPE = type(None)

# pylint: disable=undefined-variable
STRTYPE = basestring if PY2 else str

# pylint: disable=undefined-variable
UNITYPE = unicode if PY2 else str


def iteritems_(adict):
    """
    py2 to py3 helper

    :param dict adict:
    :return:
    """
    return adict.iteritems() if PY2 else adict.items()


def unicode_(astr):
    """
    py2 to py3 helper

    :param str astr:
    :return:
    """
    # pylint: disable=undefined-variable
    return unicode(astr) if PY2 else astr


def bytes_(astr):
    """
    py2 to py3 helper

    :param str astr:
    :return:
    """
    return astr.encode(ENCODING) if hasattr(astr, 'encode') else astr


def str_(astr):
    """
    py2 to py3 helper

    :param bytes astr:
    :return:
    """
    return astr.decode(ENCODING) if hasattr(astr, 'decode') else astr


def next_(itr):
    """
    py2 to py3 helper

    :param itr:
    :return:
    """
    return itr.next() if PY2 else next(itr)
