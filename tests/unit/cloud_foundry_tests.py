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

    def test_get_vcap_service_default_success(self):
        service = CloudFoundryService(self._test_vcap_services_single)
        self.assertEqual('Cloudant NoSQL DB 1', service.name)

    def test_get_vcap_service_default_success_as_dict(self):
        service = CloudFoundryService(
            json.loads(self._test_vcap_services_single)
        )
        self.assertEqual('Cloudant NoSQL DB 1', service.name)

    def test_get_vcap_service_default_failure_multiple_services(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(self._test_vcap_services_multiple)
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))

    def test_get_vcap_service_instance_host(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 1'
        )
        self.assertEqual('example.cloudant.com', service.host)

    def test_get_vcap_service_instance_password(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 1'
        )
        self.assertEqual('pa$$w0rd01', service.password)

    def test_get_vcap_service_instance_port(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 1'
        )
        self.assertEqual('1234', service.port)

    def test_get_vcap_service_instance_port_default(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 2'
        )
        self.assertEqual('443', service.port)

    def test_get_vcap_service_instance_url(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 1'
        )
        self.assertEqual('https://example.cloudant.com:1234', service.url)

    def test_get_vcap_service_instance_username(self):
        service = CloudFoundryService(
            self._test_vcap_services_multiple, 'Cloudant NoSQL DB 1'
        )
        self.assertEqual('example', service.username)

    def test_raise_error_for_missing_host(self):
        with self.assertRaises(CloudantException):
            CloudFoundryService(
                self._test_vcap_services_multiple, 'Cloudant NoSQL DB 3'
            )

    def test_raise_error_for_missing_password(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_vcap_services_multiple, 'Cloudant NoSQL DB 4'
            )
        self.assertEqual(
            "Invalid service: 'password' missing",
            str(cm.exception)
        )

    def test_raise_error_for_missing_username(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_vcap_services_multiple, 'Cloudant NoSQL DB 5'
            )
        self.assertEqual(
            "Invalid service: 'username' missing",
            str(cm.exception)
        )

    def test_raise_error_for_invalid_credentials_type(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_vcap_services_multiple, 'Cloudant NoSQL DB 6'
            )
        self.assertEqual(
            'Failed to decode VCAP_SERVICES service credentials',
            str(cm.exception)
        )

    def test_raise_error_for_missing_service(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_vcap_services_multiple, 'Cloudant NoSQL DB 7'
            )
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))

    def test_raise_error_for_invalid_vcap(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('{', 'Cloudant NoSQL DB 1')  # invalid JSON
        self.assertEqual('Failed to decode VCAP_SERVICES JSON', str(cm.exception))
