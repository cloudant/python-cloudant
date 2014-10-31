#!/usr/bin/env python
"""
_errors_

Common exception classes for cloudant python client

"""

class CloudantException(Exception):
    """
    _CloudantException_

    """
    def __init__(self, msg, code=None):
        super(CloudantException, self).__init__(msg)
        self.status_code = code

