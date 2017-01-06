#!/usr/bin/env python
# Copyright (C) 2017 IBM Corp. All rights reserved.
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
Module containing miscellaneous functions, and constants
used for unit testing.
"""
from cloudant._2to3 import PY2

# Constants

# Test long type in Python 2
LONG_NUMBER = PY2 and long(1) or 1
