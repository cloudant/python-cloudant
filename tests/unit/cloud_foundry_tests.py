#!/usr/bin/env python
# Copyright (C) 2016, 2018 IBM Corp. All rights reserved.
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
        self._test_vcap_services_single_legacy_credentials_enabled = json.dumps({'cloudantNoSQLDB': [{
                'name': 'Cloudant NoSQL DB 1',  # valid service with legacy creds enabled
                'credentials': {
                    'apikey': '1234api',
                    'username': 'user-bluemix',
                    'password': 'password',
                    'port': 443,
                    'host': 'user-bluemix.cloudant.com'
                }
            }
        ]})
        self._test_vcap_services_single = json.dumps({'cloudantNoSQLDB': [{
                'name': 'Cloudant NoSQL DB 1',  # valid service
                'credentials': {
                    'apikey': '1234api',
                    'username': 'user-bluemix',
                    'port': 443,
                    'host': 'user-bluemix.cloudant.com'
                }
            }
        ]})
        self._test_legacy_vcap_services_multiple = json.dumps({'cloudantNoSQLDB': [
            {
                'name': 'Cloudant NoSQL DB 1',  # valid legacy service
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
            },
            {
                'name': 'Cloudant NoSQL DB 7',  # missing iam api key and creds
                'credentials': {
                    'host': 'example.cloudant.com',
                    'port': 1234,
                    'username': 'example'
                }
            },
            {
                'name': 'Cloudant NoSQL DB 8',  # valid service with IAM api
                'credentials': {
                    'apikey': '1234api',
                    'username': 'example',
                    'host': 'example.cloudant.com',
                    'port': 1234
                }
            },
        ]})
        self._test_vcap_services_dedicated = json.dumps({
            'cloudantNoSQLDB Dedicated': [  # dedicated service name
                {
                    'name': 'Cloudant NoSQL DB 1',  # valid service
                    'credentials': {
                        'host': 'example.cloudant.com',
                        'password': 'pa$$w0rd01',
                        'port': 1234,
                        'username': 'example'
                    }
                }
            ]
        })

    def test_get_vcap_service_legacy_creds_success(self):
        service = CloudFoundryService(
            self._test_vcap_services_single_legacy_credentials_enabled,
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('Cloudant NoSQL DB 1', service.name)

    def test_get_vcap_service_iam_api_no_creds_success(self):
        service = CloudFoundryService(
            self._test_vcap_services_single,
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('Cloudant NoSQL DB 1', service.name)
        self.assertEqual('1234api', service.iam_api_key)
        with self.assertRaises(AttributeError) as cm:
            service.password
        self.assertEqual("'CloudFoundryService' object has no attribute '_password'", str(cm.exception))

    def test_get_vcap_service_default_success_as_dict(self):
        service = CloudFoundryService(
            json.loads(self._test_vcap_services_single_legacy_credentials_enabled),
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('Cloudant NoSQL DB 1', service.name)

    def test_get_vcap_service_default_failure_multiple_services(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))

    def test_get_vcap_service_instance_host(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 1',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('example.cloudant.com', service.host)

    def test_get_vcap_service_instance_password(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 1',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('pa$$w0rd01', service.password)

    def test_get_vcap_service_instance_port(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 1',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('1234', service.port)

    def test_get_vcap_service_instance_port_default(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 2',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('443', service.port)

    def test_get_vcap_service_instance_url(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 1',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('https://example.cloudant.com:1234', service.url)

    def test_get_vcap_service_instance_username(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 1',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('example', service.username)

    def test_get_vcap_service_instance_iam_api_key(self):
        service = CloudFoundryService(
            self._test_legacy_vcap_services_multiple,
            instance_name='Cloudant NoSQL DB 8',
            service_name='cloudantNoSQLDB'
        )
        self.assertEqual('1234api', service.iam_api_key)

    def test_raise_error_for_missing_host(self):
        with self.assertRaises(CloudantException):
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 3',
                service_name='cloudantNoSQLDB'
            )

    def test_raise_error_for_missing_password(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 4',
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual(
            'Invalid service: IAM API key or username/password credentials are required.',
            str(cm.exception)
        )

    def test_raise_error_for_missing_username(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 5',
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual(
            "Invalid service: 'username' missing",
            str(cm.exception)
        )

    def test_raise_error_for_invalid_credentials_type(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 6',
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual(
            'Failed to decode VCAP_SERVICES service credentials',
            str(cm.exception)
        )

    def test_raise_error_for_missing_iam_api_key_and_credentials(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 7',
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual(
            'Invalid service: IAM API key or username/password credentials are required.',
            str(cm.exception)
        )

    def test_raise_error_for_missing_service(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService(
                self._test_legacy_vcap_services_multiple,
                instance_name='Cloudant NoSQL DB 9',
                service_name='cloudantNoSQLDB'
            )
        self.assertEqual('Missing service in VCAP_SERVICES', str(cm.exception))

    def test_raise_error_for_invalid_vcap(self):
        with self.assertRaises(CloudantException) as cm:
            CloudFoundryService('{', 'Cloudant NoSQL DB 1')  # invalid JSON
        self.assertEqual('Failed to decode VCAP_SERVICES JSON', str(cm.exception))

    def test_get_vcap_service_with_dedicated_service_name_success(self):
        service = CloudFoundryService(
            self._test_vcap_services_dedicated,
            service_name='cloudantNoSQLDB Dedicated'
        )
        self.assertEqual('Cloudant NoSQL DB 1', service.name)
