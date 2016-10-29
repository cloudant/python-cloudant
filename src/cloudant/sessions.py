#!/usr/bin/env python
# Copyright (C) 2015, 2016 IBM Corp. All rights reserved.
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
This module provides a Session object to manage and persist settings across
database requests.
"""
import base64

from functools import wraps
from requests import Session
from urlparse import urljoin

from ._2to3 import bytes_, im_self, unicode_
from ._common_util import append_response_error_content


class CouchSession(Session):
    """
    CouchSession manages and persists settings across all requests.

    :param str username: username
    :param str password: password
    :param str server_url: URL of CouchDB server
    :param object adapter: custom transport adapter
    :param bool admin_party: enable admin party mode
    :param dict headers: default headers to persist across all requests
    """

    def __new__(cls, *args, **kwargs):
        couch_session = super(CouchSession, cls).__new__(cls, *args, **kwargs)

        # CouchDB only renews the cookie if we're within 10% of the end of the
        # timeout window. Failing to submit a request during this time will
        # result in the cookie not being renewed. To avoid this we catch all
        # 401 'unauthorized' responses and retry following a renewed session
        # login.

        for verb in ['DELETE', 'GET', 'HEAD', 'POST', 'PUT']:
            setattr(couch_session, verb.lower(), cls.renew_cookie_decorator(
                getattr(couch_session, verb.lower())
            ))

        return couch_session

    def __init__(self,
                 username,
                 password,
                 server_url,
                 adapter=None,
                 admin_party=False,
                 headers=None):
        super(CouchSession, self).__init__()

        self.username = username
        self.password = password

        self.admin_party = admin_party
        self.session_url = urljoin(server_url, '_session')

        if headers:
            self.headers.update(headers)

        # If a Transport Adapter was supplied add it to the session
        if adapter:
            self.mount(server_url, adapter)

        # Utilize an event hook to append to the response message
        self.hooks['response'].append(append_response_error_content)

    @property
    def basic_auth_str(self):
        """
        Get Base64 authentication string.

        :return: Base64 username:password encoding as string
        """
        if self.admin_party:
            return None

        # Base64 encode username:password
        hash_ = base64.urlsafe_b64encode(bytes_('{username}:{password}'.format(
            username=self.username,
            password=self.password
        )))
        return 'Basic {0}'.format(unicode_(hash_))

    @property
    def cookie(self):
        """
        Session cookie.

        :return: session cookie as string
        """
        return self.cookies.get('AuthSession')

    def get_session_info(self):
        """
        Retrieves information about the current login session to verify data
        related to sign in.

        :returns: Dictionary of session info for the current session.
        """
        if self.admin_party:
            return None

        resp = self.get(self.session_url)
        resp.raise_for_status()
        return resp.json()

    def is_authenticated(self):
        """
        Check the session cookie is authenticated.

        :return: is authenticated as boolean
        """
        if self.admin_party:
            return True

        session_user = self.get_session_info().get('userCtx', {}).get('name')
        return self.username == session_user

    def login(self):
        """ Session login. """
        if self.admin_party:
            return

        self.cookies.clear()  # clear session cookies
        resp = self.post(
            self.session_url,
            data={'name': self.username, 'password': self.password},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        resp.raise_for_status()

    def logout(self):
        """ Session logout. """
        if self.admin_party:
            return

        resp = self.delete(self.session_url)
        resp.raise_for_status()

    @classmethod
    def renew_cookie_decorator(cls, function):
        """
        Decorator to renew authentication cookie on 401 response.

        :param function: session function
        """
        @wraps(function)
        def wrapper(*args, **kwargs):
            session = im_self(function)
            result = function(*args, **kwargs)

            try:
                if result.status_code == 401 and not session.is_authenticated():
                    session.login()  # renew cookie
                    result = function(*args, **kwargs)

            except Exception:
                pass  # ignore failure

            finally:
                return result

        return wrapper
