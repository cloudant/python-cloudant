#!/usr/bin/env python
# Copyright (c) 2018 IBM Corp. All rights reserved.
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
TODO
"""

import unittest
import requests
import json
import mock

from cloudant.scheduler import Scheduler

from .unit_t_db_base import UnitTestDbBase

class SchedulerTests(UnitTestDbBase):

    def setUp(self):
        """
        Set up test attributes
        """
        super(SchedulerTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(SchedulerTests, self).tearDown()
    
    def test_scheduler_docs(self):
        """
        Test scheduler docs
        """
        # set up mock response using a real captured response
        m_response_ok = requests.Response()
        m_response_ok.status_code = 200
        m_response_ok.json = {"total_rows":6,"offset":0,"docs":[
            {"database":"tomblench/_replicator",
             "doc_id":"296e48244e003eba8764b2156b3bf302","id":None,
             "source":"https://tomblench.cloudant.com/animaldb/",
             "target":"https://tomblench.cloudant.com/animaldb_copy/",
             "state":"completed","error_count":0,"info":{"revisions_checked":15,
                                                         "missing_revisions_found":2,"docs_read":2,"docs_written":2,
                                                         "changes_pending":None,"doc_write_failures":0,
                                                         "checkpointed_source_seq":"19-g1AAAAGjeJyVz10KwjAMB_BoJ4KX8AZF2tWPJ3eVpqnO0XUg27PeTG9Wa_VhwmT6kkDIPz_iACArGcGS0DRnWxDmHE9HdJ3lxjUdad9yb1sXF6cacB9CqEqmZ3UczKUh2uGhHxeD8U9i_Z3AIla8vJVJUlBIZYTqX5A_KMM7SfFZrHCNLUK3p7RIkl5tSRD-K6kx6f6S0k8sScpYJTb5uFQ9AI9Ch9c"},"start_time":None,"last_updated":"2017-04-13T14:53:50+00:00"},
            {"database":"tomblench/_replicator",
             "doc_id":"3b749f320867d703550b0f758a4000ae","id":None,
             "source":"https://examples.cloudant.com/animaldb/",
             "target":"https://tomblench.cloudant.com/animaldb/","state":"completed",
             "error_count":0,"info":{"revisions_checked":15,
                                     "missing_revisions_found":15,"docs_read":15,"docs_written":15,
                                     "changes_pending":None,"doc_write_failures":0,
                                     "checkpointed_source_seq":"56-g1AAAAGveJzLYWBgYMlgTmFQSElKzi9KdUhJstDLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMiby5QgN04JS3FLDUJWb8Jdv0gSxThigyN8diS5AAkk-qhFvFALEo2MTEwMSXGDDSbTPHYlMcCJBkagBTQsv0g28TBtpkbGCQapaF4C4cxJFt2AGIZ2GscYMuMDEzMUizMkC0zw25MFgBKoovi"},"start_time":None,"last_updated":"2017-04-27T12:28:44+00:00"},
            {"database":"tomblench/_replicator",
             "doc_id":"ad8f7896480b8081c8f0a2267ffd1859","id":None,
             "source":"https://tortytherlediffecareette:*****@mikerhodestesty008.cloudant.com/moviesdb/","target":"https://tomblench.cloudant.com/moviesdb_rep/",
             "state":"completed","error_count":0,"info":{"revisions_checked":5997,
                                                         "missing_revisions_found":5997,"docs_read":5997,"docs_written":5997,
                                                         "changes_pending":None,"doc_write_failures":0,
                                                         "checkpointed_source_seq":"5997-g1AAAANreJy10UEKwjAQAMBgBcVP2BeUpEm1PdmfaDYJSKkVtB486U_0J_oBTz5AHyAI3jxIjUml1x7ayy67LDssmyKE-nNHIleCWK5ULIF6uVrnW4xDT6TLjeRZ7mUqT_VkhyMYFkWRzB3Q1XOhez3iczKKghor6jvg6giTiroYiuNQYYqbpeIfNa2oh72KhQGosFlq9qN2FfUyFPgUCKONoneXR7TXSWuHkvsYjjEWjQVvgTta7lRyV_szKgmRbVx3ttzNcs7AcEoKCHAb3N1y_9-9DYeBYzEiNTYlX3EcE0s"},"start_time":None,"last_updated":"2016-08-23T13:11:26+00:00"},
            {"database":"tomblench/_replicator",
             "doc_id":"b63c053ecd95a4047b55ed8847b046f1","id":None,
             "source":"https://tomblench.cloudant.com/atestdb2/",
             "target":"https://tomblench.cloudant.com/atestdb1/","state":"completed",
             "error_count":0,"info":{"revisions_checked":1,
                                     "missing_revisions_found":1,"docs_read":1,"docs_written":1,
                                     "changes_pending":None,"doc_write_failures":0,
                                     "checkpointed_source_seq":"2-g1AAAAFHeJyNjkEOgjAQRSdAYjyFN2jSFCtdyVU6nSKQWhJC13ozvVktsoEF0c2fTPL_-98BQNHmBCdCM4y2JuQMuxu6YJlxQyDtJ-bt5JIx04DXGGOvYRsR-xGsk-JjTrW5hnv6Dg0XplRngmPwZJvOW9ry5D7PF0nhmU5CvmZm9mVKVVacLr8pfy9fmt5L02q9qEhJbtbr-w-AQmfD"},"start_time":None,"last_updated":"2017-05-16T16:25:22+00:00"},
            {"database":"tomblench/_replicator",
             "doc_id":"c71c9e69e30a182dc91d8938277bc85e","id":None,
             "source":"https://tomblench.cloudant.com/animaldb/",
             "target":"https://tomblench.cloudant.com/animaldb_copy/",
             "state":"completed","error_count":0,"info":{"revisions_checked":15,
                                                         "missing_revisions_found":15,"docs_read":15,"docs_written":15,
                                                         "changes_pending":None,"doc_write_failures":0,
                                                         "checkpointed_source_seq":"14-g1AAAAEueJzLYWBgYMlgTmGQSUlKzi9KdUhJMtTLTU1M0UvOyS9NScwr0ctLLckBqmJKZEiy____f1YGUyJrLlCAPdHEPCktJZk43UkOQDKpHmoAI9gAw2STxCTzJOIMyGMBkgwNQApoxv6sDGaoK0yN04wsk80IGEGKHQcgdoAdygxxaIplklFaWhYAu2FdOA"},"start_time":None,"last_updated":"2015-05-12T11:47:33+00:00"},
            {"database":"tomblench/_replicator",
             "doc_id":"e6242d1e9ce059b0388fc75af3116a39","id":None,
             "source":"https://tomblench.cloudant.com/atestdb1/",
             "target":"https://tomblench.cloudant.com/atestdb2/","state":"completed",
             "error_count":0,"info":{"revisions_checked":1,
                                     "missing_revisions_found":1,"docs_read":1,"docs_written":1,
                                     "changes_pending":None,"doc_write_failures":0,
                                     "checkpointed_source_seq":"1-g1AAAAFheJyFzkEOgjAQBdBRSIyn8AZNgEJgJVeZ6bQCqSUhdK0305th1Q1dEDYzyWTy_rcAkHYJw4VJjZNumQpB_Y2s10LZ0TO6WTg92_B4RKDrsixDlyDcw-FUVUiFahjO3rE2vdMcY9k2Rm2Y9Ig8bWqspdz25Lbn0jDhGVYgX1_z8DMblnlp8n0lTir3kt7_pFV7NE2WYbluP3wATr5vQA"},"start_time":None,"last_updated":"2017-05-16T16:24:02+00:00"}
        ]}

        self.client.r_session.get = mock.Mock(return_value=m_response_ok)
        scheduler = Scheduler(self.client)
        response = scheduler.list_docs(skip=0, limit=10)
        # assert on request and response
        self.client.r_session.get.assert_called_with(
            self.url + '/_scheduler/docs',
            params={"skip":0, "limit":10},
        )
        self.assertEqual(response.json["total_rows"], 6)

    def test_scheduler_jobs(self):
        """
        Test scheduler jobs
        """
        # set up mock response using a real captured response
        m_response_ok = requests.Response()
        m_response_ok.status_code = 200
        m_response_ok.json = {"total_rows":1,"offset":0,
                              "jobs":[{"database":None,
                                       "id":"f11105eaaded4981d21ff8ebf846f48b+create_target",
                                       "pid":"<0.5866.6800>",
                                       "source":"https://clientlibs-test:*****@clientlibs-test.cloudant.com/largedb1g/",
                                       "target":"https://tomblench:*****@tomblench.cloudant.com/largedb1g/",
                                       "user":"tomblench",
                                       "doc_id":None,
                                       "history":[{"timestamp":"2018-04-12T13:06:20Z","type":"started"},
                                                  {"timestamp":"2018-04-12T13:06:20Z","type":"added"}],
                                       "node":"dbcore@db2.bigblue.cloudant.net",
                                       "start_time":"2018-04-12T13:06:20Z"}]}        
        self.client.r_session.get = mock.Mock(return_value=m_response_ok)
        scheduler = Scheduler(self.client)
        response = scheduler.list_jobs(skip=0, limit=10)
        # assert on request and response
        self.client.r_session.get.assert_called_with(
            self.url + '/_scheduler/jobs',
            params={"skip":0, "limit":10},
        )
        self.assertEqual(response.json["total_rows"], 1)
