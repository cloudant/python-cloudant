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
Module that contains common exception classes for the Cloudant Python client
library.
"""

class CloudantException(Exception):
    """
    Provides a way to issue Cloudant Python client library specific exceptions.
    A CloudantException object is instantiated with a message and optional code.

    Note:  The intended use for this class is internal to the Cloudant Python
    client library.

    :param str msg: A message that describes the exception.
    :param int code: A code value used to identify the exception.
    """
    def __init__(self, msg, code=None):
        super(CloudantException, self).__init__(msg)
        self.status_code = code


class CloudantArgumentError(CloudantException):
    """
    Provides a way to issue Cloudant Python client library specific exceptions
    that pertain to invalid argument errors.  A CloudantArgumentError object is
    instantiated with a message and optional code where the code defaults to
    400.

    Note:  The intended use for this class is internal to the Cloudant Python
    client library.

    :param str msg: A message that describes the exception.
    :param int code: An optional code value used to identify the exception.
        Defaults to 400.
    """
    def __init__(self, msg, code=400):
        super(CloudantArgumentError, self).__init__(msg, code)
