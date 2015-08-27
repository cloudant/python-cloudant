#!/usr/bin/env python
"""
_changes tests_

Tests for the changes module

"""
import requests
import unittest
import mock
from cloudant.changes import Feed


FIXTURE_DATA = """
{"seq":"26982-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUIbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4GmyfpblpiqmZMREmZQEAyF2OgA","id":"2014-02-23T04:10:49.959636Z","changes":[{"rev":"1-3ad766b6a1abf113057e7b83285f53e2"}]}
{"seq":"26983-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUIbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4BmyfpblpiqmZMREmZQEAyI6OgQ","id":"2014-02-23T05:35:21.339700Z","changes":[{"rev":"1-1cc5c21ea8542c4b26f5e6bd0ff647a8"}]}
{"seq":"26984-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUYbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4BmyfpblpiqmZMREmZQEAyaCOgg","id":"2014-02-23T05:24:10.461091Z","changes":[{"rev":"1-fe8a17663810f6d4d1069c1f4324326e"}]}

{"seq":"26985-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUEbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4BmyfpblpiqmZMREmZQEAyrKOgw","id":"2014-02-23T05:24:10.623315Z","changes":[{"rev":"1-1a89e364faff1f920e445974f413bdad"}]}
{"seq":"26986-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUUbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4BmyfpblpiqmZMREmZQEAy8SOhA","id":"2014-02-23T05:24:11.979233Z","changes":[{"rev":"1-8c9473713df60fc3f937331384591eee"}]}
{"seq":"26987-g1AAAAG7eJzLYWBgYMlgTmFQSElKzi9KdUhJstTLTS3KLElMT9VLzskvTUnMK9HLSy3JAapkSmRIsv___39WBnMSA4PUtlygGLtZqkWqQaoZEUaA7FGEKzI0xWNRkgOQTKpH2PUMbJeRpWmqaYoJMcagWWaCx7I8FiDJ0ACkgPbth1goyQy2MCUxxdjC2IIYo4gPRYh9ByD2wTx4BmyfpblpiqmZMREmZQEAzNaOhQ","id":"2014-02-23T05:24:12.103794Z","changes":[{"rev":"1-ea8c80294e50df6f15f164baaf6280ba"}]}

BADJSONLINE

"""



class FeedTests(unittest.TestCase):

    def setUp(self):
        """
        mock out requests.Session
        """
        self.patcher = mock.patch.object(requests, "Session")
        self.mock_session = self.patcher.start()
        self.mock_instance = mock.Mock()
        self.mock_instance.auth = None
        self.mock_instance.headers = {}
        self.mock_instance.cookies = {'AuthSession': 'COOKIE'}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.post = mock.Mock()
        self.mock_instance.delete = mock.Mock()
        self.mock_instance.put = mock.Mock()
        self.mock_session.return_value = self.mock_instance
        self.username = "steve"
        self.password = "abc123"

    def tearDown(self):
        self.patcher.stop()

    def test_feed(self):
        """
        test iterating over a mocked feed
        """
        mock_iter = (x for x in FIXTURE_DATA.split('\n'))
        mock_resp = mock.Mock()
        mock_resp.iter_lines = mock.Mock()
        mock_resp.iter_lines.return_value = mock_iter

        self.mock_instance.get.return_value = mock_resp

        f = Feed(
            self.mock_instance,
            "http://bob.cloudant.com/bobsdb/_changes",
            include_docs=True,
            since="SINCE"
        )

        result = [x for x in f]
        # 5 empty lines
        self.assertEqual(result.count({}), 5)
        # six non empty lines
        changes = [
            x['changes'] for x in result if x.get('changes') is not None
        ]
        self.assertEqual(len(changes), 6)

        errors = [x['error'] for x in result if x.get('error') is not None]
        self.assertEqual(len(errors), 1)

if __name__ == '__main__':
    unittest.main()
