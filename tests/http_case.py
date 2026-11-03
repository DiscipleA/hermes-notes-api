"""Real loopback HTTP fixture, shared by baseline and presentation tests."""
import http.client
from http.server import HTTPServer
import json
import threading
import unittest

from notes_api import make_handler


class HTTPTestCase(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), make_handler())
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        self.thread.start()
        self.addCleanup(self.thread.join, 2)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path="/notes", payload=None, raw=None, headers=None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else raw
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            content = response.read()
            result = json.loads(content) if content else None
            return response.status, result, dict(response.getheaders())
        finally:
            connection.close()

    def create(self, text):
        status, note, _ = self.request("POST", payload={"text": text})
        self.assertEqual(status, 201)
        return note

    def assert_empty(self):
        status, body, _ = self.request("GET")
        self.assertEqual((status, body), (200, {"notes": []}))
