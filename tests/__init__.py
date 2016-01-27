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
_tests_

Test coverage for package

"""
import sys

PY2 = sys.version_info[0] < 3

def unicode_(s):
    return unicode(s) if PY2 else s

def iteritems_(d):
    return d.iteritems() if PY2 else d.items()

def bytes_(astr):
    return astr.encode('utf-8') if hasattr(astr, 'encode') else astr

def str_(astr):
    return astr.decode('utf-8') if hasattr(astr, 'decode') else astr

