#!/usr/bin/env python
"""
_cloudant_

Cloudant Python Client API

"""
__version__="0.0.4"

import contextlib

from .account import Cloudant


@contextlib.contextmanager
def cloudant(user, passwd, **kwargs):
    """
    _cloudant_

    Context helper to create a cloudant session and
    provide access to databases, docs etc.

    """
    c = Cloudant(user, passwd, **kwargs)
    c.connect()
    yield c
    c.disconnect()
