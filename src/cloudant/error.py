#!/usr/bin/env python
# Copyright (c) 2015, 2016 IBM. All rights reserved.
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
from cloudant._messages import (
    ARGUMENT_ERROR,
    CLIENT,
    DATABASE,
    DESIGN_DOCUMENT,
    DOCUMENT,
    FEED,
    INDEX,
    REPLICATOR,
    RESULT,
    VIEW)

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
    that pertain to invalid argument errors.

    Note:  The intended use for this class is internal to the Cloudant Python
    client library.

    :param int code: An optional code value used to identify the exception.
        Defaults to 100.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = ARGUMENT_ERROR[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = ARGUMENT_ERROR[code]
        super(CloudantArgumentError, self).__init__(msg, code)

class ResultException(CloudantException):
    """
    Provides a way to issue Cloudant Python client library result specific
    exceptions.

    :param int code: A code value used to identify the result exception.
        Defaults to 100.
    :param args: A list of arguments used to format the exception message.
    """

    def __init__(self, code=100, *args):
        try:
            msg = RESULT[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = RESULT[code]
        super(ResultException, self).__init__(msg, code)


class CloudantClientException(CloudantException):
    """
    Provides a way to issue Cloudant library client specific exceptions.

    :param int code: A code value used to identify the client exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = CLIENT[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = CLIENT[code]
        super(CloudantClientException, self).__init__(msg, code)

class CloudantDatabaseException(CloudantException):
    """
    Provides a way to issue Cloudant library database specific exceptions.

    :param int code: A code value used to identify the database exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            if code in DATABASE:
                msg = DATABASE[code].format(*args)
            elif isinstance(code, int):
                msg = ' '.join(args)
            else:
                code = 100
                msg = DATABASE[code]
        except (KeyError, IndexError):
            code = 100
            msg = DATABASE[code]
        super(CloudantDatabaseException, self).__init__(msg, code)

class CloudantDesignDocumentException(CloudantException):
    """
    Provides a way to issue Cloudant library design document exceptions.

    :param int code: A code value used to identify the design doc exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = DESIGN_DOCUMENT[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = DESIGN_DOCUMENT[code]
        super(CloudantDesignDocumentException, self).__init__(msg, code)

class CloudantDocumentException(CloudantException):
    """
    Provides a way to issue Cloudant library document specific exceptions.

    :param int code: A code value used to identify the document exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = DOCUMENT[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = DOCUMENT[code]
        super(CloudantDocumentException, self).__init__(msg, code)

class CloudantFeedException(CloudantException):
    """
    Provides a way to issue Cloudant library feed specific exceptions.

    :param int code: A code value used to identify the feed exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = FEED[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = FEED[code]
        super(CloudantFeedException, self).__init__(msg, code)

class CloudantIndexException(CloudantException):
    """
    Provides a way to issue Cloudant library index specific exceptions.

    :param int code: A code value used to identify the index exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = INDEX[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = INDEX[code]
        super(CloudantIndexException, self).__init__(msg, code)

class CloudantReplicatorException(CloudantException):
    """
    Provides a way to issue Cloudant library replicator specific exceptions.

    :param int code: A code value used to identify the replicator exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = REPLICATOR[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = REPLICATOR[code]
        super(CloudantReplicatorException, self).__init__(msg, code)

class CloudantViewException(CloudantException):
    """
    Provides a way to issue Cloudant library view specific exceptions.

    :param int code: A code value used to identify the view exception.
    :param args: A list of arguments used to format the exception message.
    """
    def __init__(self, code=100, *args):
        try:
            msg = VIEW[code].format(*args)
        except (KeyError, IndexError):
            code = 100
            msg = VIEW[code]
        super(CloudantViewException, self).__init__(msg, code)
