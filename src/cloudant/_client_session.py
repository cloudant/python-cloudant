#!/usr/bin/env python
# Copyright (c) 2015, 2019 IBM Corp. All rights reserved.
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
Module containing client session classes.
"""
import base64
import json
import os

from requests import RequestException, Session

from ._2to3 import bytes_, unicode_, url_join
from ._common_util import response_to_json_dict
from .error import CloudantException


class ClientSession(Session):
    """
    This class extends Session and provides a default timeout.
    """

    def __init__(self, username=None, password=None, session_url=None, **kwargs):
        super(ClientSession, self).__init__()

        self._username = username
        self._password = password
        self._session_url = session_url

        self._auto_renew = kwargs.get('auto_renew', False)
        self._timeout = kwargs.get('timeout', None)

    def base64_user_pass(self):
        """
        Composes a basic http auth string, suitable for use with the
        _replicator database, and other places that need it.

        :returns: Basic http authentication string
        """
        if self._username is None or self._password is None:
            return None

        hash_ = base64.urlsafe_b64encode(bytes_("{username}:{password}".format(
            username=self._username,
            password=self._password
        )))
        return "Basic {0}".format(unicode_(hash_))

    # pylint: disable=arguments-differ
    def request(self, method, url, **kwargs):
        """
        Overrides ``requests.Session.request`` to set the timeout.
        """
        resp = super(ClientSession, self).request(
            method, url, timeout=self._timeout, **kwargs)

        return resp

    def info(self):
        """
        Get session information.
        """
        if self._session_url is None:
            return None

        resp = self.get(self._session_url)
        resp.raise_for_status()
        return response_to_json_dict(resp)

    def set_credentials(self, username, password):
        """
        Set a new username and password.

        :param str username: New username.
        :param str password: New password.
        """
        if username is not None:
            self._username = username

        if password is not None:
            self._password = password

    def login(self):
        """
        No-op method - not implemented here.
        """
        # pylint: disable=unnecessary-pass
        pass

    def logout(self):
        """
        No-op method - not implemented here.
        """
        # pylint: disable=unnecessary-pass
        pass


class BasicSession(ClientSession):
    """
    This class extends ClientSession to provide basic access authentication.
    """

    def __init__(self, username, password, server_url, **kwargs):
        super(BasicSession, self).__init__(
            username=username,
            password=password,
            session_url=url_join(server_url, '_session'),
            **kwargs)

    def request(self, method, url, **kwargs):
        """
        Overrides ``requests.Session.request`` to provide basic access
        authentication.
        """
        auth = None
        if self._username is not None and self._password is not None:
            auth = (self._username, self._password)

        return super(BasicSession, self).request(
            method, url, auth=auth, **kwargs)


class CookieSession(ClientSession):
    """
    This class extends ClientSession and provides cookie authentication.
    """

    def __init__(self, username, password, server_url, **kwargs):
        super(CookieSession, self).__init__(
            username=username,
            password=password,
            session_url=url_join(server_url, '_session'),
            **kwargs)

    def login(self):
        """
        Perform cookie based user login.
        """
        resp = super(CookieSession, self).request(
            'POST',
            self._session_url,
            data={'name': self._username, 'password': self._password},
        )
        resp.raise_for_status()

    def logout(self):
        """
        Logout cookie based user.
        """
        resp = super(CookieSession, self).request('DELETE', self._session_url)
        resp.raise_for_status()

    def request(self, method, url, **kwargs):
        """
        Overrides ``requests.Session.request`` to renew the cookie and then
        retry the original request (if required).
        """
        resp = super(CookieSession, self).request(method, url, **kwargs)

        if not self._auto_renew:
            return resp

        is_expired = any((
            resp.status_code == 403 and
            response_to_json_dict(resp).get('error') == 'credentials_expired',
            resp.status_code == 401
        ))

        if is_expired:
            self.login()
            resp = super(CookieSession, self).request(method, url, **kwargs)

        return resp


class IAMSession(ClientSession):
    """
    This class extends ClientSession and provides IAM authentication.
    """

    def __init__(self, api_key, server_url, client_id=None, client_secret=None,
                 **kwargs):
        super(IAMSession, self).__init__(
            session_url=url_join(server_url, '_iam_session'),
            **kwargs)

        self._api_key = api_key
        self._token_url = os.environ.get(
            'IAM_TOKEN_URL', 'https://iam.cloud.ibm.com/identity/token')
        self._token_auth = None
        if client_id and client_secret:
            self._token_auth = (client_id, client_secret)

    @property
    def get_api_key(self):
        """
        Get IAM API key.

        :return: IAM API key.
        """
        return self._api_key

    def login(self):
        """
        Perform IAM cookie based user login.
        """
        access_token = self._get_access_token()
        try:
            super(IAMSession, self).request(
                'POST',
                self._session_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'access_token': access_token})
            ).raise_for_status()

        except RequestException:
            raise CloudantException(
                'Failed to exchange IAM token with Cloudant')

    def logout(self):
        """
        Logout IAM cookie based user.
        """
        self.cookies.clear()

    def request(self, method, url, **kwargs):
        """
        Overrides ``requests.Session.request`` to renew the IAM cookie
        and then retry the original request (if required).
        """
        # The CookieJar API prevents callers from getting an individual Cookie
        # object by name.
        # We are forced to use the only exposed method of discarding expired
        # cookies from the CookieJar. Internally this involves iterating over
        # the entire CookieJar and calling `.is_expired()` on each Cookie
        # object.
        self.cookies.clear_expired_cookies()

        if self._auto_renew and 'IAMSession' not in self.cookies.keys():
            self.login()

        resp = super(IAMSession, self).request(method, url, **kwargs)

        if not self._auto_renew:
            return resp

        if resp.status_code == 401:
            self.login()
            resp = super(IAMSession, self).request(method, url, **kwargs)

        return resp

    # pylint: disable=arguments-differ, unused-argument
    def set_credentials(self, username, api_key):
        """
        Set a new IAM API key.

        :param str username: Username parameter is unused.
        :param str api_key: New IAM API key.
        """
        if api_key is not None:
            self._api_key = api_key

    def _get_access_token(self):
        """
        Get IAM access token using API key.
        """
        err = 'Failed to contact IAM token service'
        try:
            resp = super(IAMSession, self).request(
                'POST',
                self._token_url,
                auth=self._token_auth,
                headers={'Accepts': 'application/json'},
                data={
                    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                    'response_type': 'cloud_iam',
                    'apikey': self._api_key
                }
            )
            err = response_to_json_dict(resp).get('errorMessage', err)
            resp.raise_for_status()

            return response_to_json_dict(resp)['access_token']

        except KeyError:
            raise CloudantException('Invalid response from IAM token service')

        except RequestException:
            raise CloudantException(err)
