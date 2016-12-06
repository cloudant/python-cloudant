#!/usr/bin/env python
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
_cloud_foundry_tests_

Unit tests for the CloudFoundryService class.
"""

import json
import mock
import unittest

from cloudant._common_util import CloudFoundryService
from cloudant.error import CloudantException


class CloudFoundryServiceTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(CloudFoundryServiceTests, self).__init__(*args, **kwargs)
        self._test_vcap_services_single = json.dumps({'cloudantNoSQLDB': [
            {
                'name': 'Cloudant NoSQL DB 1',  # valid service
                'credentials': {
                    'host': 'example.cloudant.com',
                    'password': 'pa$$w0rd01',
                    'port': 1234,
                    'username': 'example'
                }
            }
        ]})
        self._test_vcap_services_multiple = json.dumps({'cloudantNoSQLDB': [
            {
                'name': 'Cloudant NoSQL DB 1',  # valid service
                'credentials': {
                    'host': 'example.cloudant.com',
                    'password': 'pa$$w0rd01',
                    'port': 1234,
                    'username': 'example'
                }
            },
            {
                'name': 'Cloudant NoSQL DB 2',  # valid service, default port
                'credentials': {
                    'host': 'example.cloudant.com',
                    'password': 'pa$$w0rd01',
                    'username': 'example'
                }
            },
            {
                'name': 'Cloudant NoSQL DB 3',  # missing host
                'credentials': {
                    'password': 'pa$$w0rd01',
                    'port': 1234,
                    'username': 'example'
                }
            },
            {
                'name': 'Cloudant NoSQL DB 4',  # missing password
                'credentials': {
                    'host': 'example.cloudant.com',
                    'port': 1234,
                    'username': 'example'
                }
            },
            {
                'name': 'Cloudant NoSQL DB 5',  # missing username
                'credentials': {
                    'host': 'example.cloudant.com',
                    'password': 'pa$$w0rd01',
                    'port': 1234,
                }
            },
            {
                'name': 'Cloudant NoSQL DB 6',  # invalid credentials type
                'credentials': [
                    'example.cloudant.com',
                    'pa$$w0rd01',
                    'example'
                ]
            }
        ]})

    @mock.patch('os.getenv')
    def test_get_vcap_service_default_success(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_single
        service = CloudFoundryService()
        self.assertEqual('Cloudant NoSQL DB 1', service.name)

    @mock.patch('os.getenv')
    def test_get_vcap_service_default_failure_multiple_services(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService()
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_host(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 1')
        self.assertEqual('example.cloudant.com', service.host)

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_password(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 1')
        self.assertEqual('pa$$w0rd01', service.password)

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_port(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 1')
        self.assertEqual('1234', service.port)

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_port_default(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 2')
        self.assertEqual('443', service.port)

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_url(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 1')
        self.assertEqual('https://example.cloudant.com:1234', service.url)

    @mock.patch('os.getenv')
    def test_get_vcap_service_instance_username(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        service = CloudFoundryService('Cloudant NoSQL DB 1')
        self.assertEqual('example', service.username)

    @mock.patch('os.getenv')
    def test_raise_error_for_missing_host(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException):
            CloudFoundryService('Cloudant NoSQL DB 3')

    @mock.patch('os.getenv')
    def test_raise_error_for_missing_password(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('Cloudant NoSQL DB 4')
        self.assertEqual(
            "Invalid service: 'password' missing",
            str(cm.exception)
        )

    @mock.patch('os.getenv')
    def test_raise_error_for_missing_username(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('Cloudant NoSQL DB 5')
        self.assertEqual(
            "Invalid service: 'username' missing",
            str(cm.exception)
        )

    @mock.patch('os.getenv')
    def test_raise_error_for_invalid_credentials_type(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('Cloudant NoSQL DB 6')
        self.assertEqual(
            'Failed to decode VCAP_SERVICES service credentials',
            str(cm.exception)
        )

    @mock.patch('os.getenv')
    def test_raise_error_for_missing_service(self, m_getenv):
        m_getenv.return_value = self._test_vcap_services_multiple
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('Cloudant NoSQL DB 7')
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))
