import http.client
import unittest

from notes_api import DEFAULT_HOST, MAX_BODY_BYTES
from tests.http_case import HTTPTestCase


class NotesAPITests(HTTPTestCase):
    def test_list_starts_empty(self):
        self.assert_empty()

    def test_create_returns_note(self):
        status, note, _ = self.request("POST", payload={"text": "First note"})
        self.assertEqual((status, note), (201, {"id": 1, "text": "First note"}))

    def test_list_returns_created_notes_in_order(self):
        notes = [self.create("One"), self.create("Two")]
        status, body, _ = self.request("GET")
        self.assertEqual((status, body), (200, {"notes": notes}))

    def test_valid_text_preserves_surrounding_whitespace(self):
        text = "  Keep my spacing\n"
        self.assertEqual(self.create(text)["text"], text)
        self.assertEqual(self.request("GET")[1]["notes"][0]["text"], text)

    def test_unicode_text_round_trips(self):
        text = "Caf\u00e9 \u270d"
        self.assertEqual(self.create(text)["text"], text)

    def test_delete_returns_no_content(self):
        note = self.create("Delete me")
        status, body, headers = self.request("DELETE", f"/notes/{note['id']}")
        self.assertEqual((status, body, headers["Content-Length"]), (204, None, "0"))
        self.assert_empty()

    def test_delete_only_removes_target(self):
        first = self.create("One")
        second = self.create("Two")
        self.request("DELETE", f"/notes/{first['id']}")
        self.assertEqual(self.request("GET")[1], {"notes": [second]})

    def test_ids_are_not_reused(self):
        first = self.create("One")
        self.request("DELETE", f"/notes/{first['id']}")
        second = self.create("Two")
        self.assertGreater(second["id"], first["id"])

    def test_delete_missing_note_returns_404(self):
        self.assertEqual(self.request("DELETE", "/notes/999")[0], 404)

    def test_delete_malformed_ids_returns_404(self):
        for path in ("/notes/nope", "/notes/-1", "/notes/0", "/notes/1/extra"):
            with self.subTest(path=path):
                self.assertEqual(self.request("DELETE", path)[0], 404)

    def test_unknown_paths_return_404(self):
        for method in ("GET", "POST", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.request(method, "/missing")[0], 404)

    def test_empty_text_is_rejected_without_mutation(self):
        self.assertEqual(self.request("POST", payload={"text": ""})[0], 400)
        self.assert_empty()

    def test_missing_text_is_rejected(self):
        self.assertEqual(self.request("POST", payload={"other": "note"})[0], 400)
        self.assert_empty()

    def test_non_string_text_is_rejected(self):
        for text in (None, False, 42, [], {}):
            with self.subTest(text=text):
                self.assertEqual(self.request("POST", payload={"text": text})[0], 400)
        self.assert_empty()

    def test_non_object_json_is_rejected(self):
        for raw in (b"[]", b'"note"', b"null", b"42"):
            with self.subTest(raw=raw):
                self.assertEqual(self.request("POST", raw=raw)[0], 400)
        self.assert_empty()

    def test_malformed_json_is_rejected(self):
        for raw in (b'{"text":', b"", b'{"text":"one"} trailing'):
            with self.subTest(raw=raw):
                status, body, _ = self.request("POST", raw=raw)
                self.assertEqual(status, 400)
                self.assertIn("error", body)
        self.assert_empty()

    def test_integer_digit_limit_json_is_rejected_without_mutation(self):
        existing = self.create("Before malformed JSON")
        raw = b'{"text":"fine","extra":' + b"9" * 5000 + b"}"
        self.assertLess(len(raw), MAX_BODY_BYTES)
        try:
            status, body, _ = self.request("POST", raw=raw)
        except http.client.RemoteDisconnected:
            self.fail("Expected HTTP 400 for oversized JSON integer, not a disconnect")
        self.assertEqual((status, body), (400, {"error": "Malformed JSON body"}))
        self.assertEqual(self.request("GET")[:2], (200, {"notes": [existing]}))
        following = self.create("After malformed JSON")
        self.assertEqual(following["id"], existing["id"] + 1)
        self.assertEqual(self.request("GET")[:2], (200, {"notes": [existing, following]}))

    def test_invalid_utf8_is_rejected(self):
        self.assertEqual(self.request("POST", raw=b'{"text":"\xff"}')[0], 400)
        self.assert_empty()

    def test_non_json_content_type_is_rejected(self):
        self.assertEqual(self.request("POST", raw=b"text", headers={"Content-Type": "text/plain"})[0], 415)
        self.assert_empty()

    def test_body_over_size_limit_is_rejected(self):
        self.assertEqual(self.request("POST", raw=b"x" * (MAX_BODY_BYTES + 1))[0], 413)
        self.assert_empty()

    def test_body_exactly_at_limit_is_accepted(self):
        text = "x" * (MAX_BODY_BYTES - len(b'{"text":""}'))
        raw = b'{"text":"' + text.encode("ascii") + b'"}'
        self.assertEqual(len(raw), MAX_BODY_BYTES)
        status, note, _ = self.request("POST", raw=raw)
        self.assertEqual((status, note["text"]), (201, text))

    def test_invalid_content_length_is_rejected(self):
        for value in ("-1", "nope", "+1"):
            with self.subTest(value=value):
                status, _, _ = self.request("POST", raw=b"", headers={"Content-Length": value})
                self.assertEqual(status, 400)
        self.assert_empty()

    def test_missing_content_length_is_rejected(self):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        try:
            connection.putrequest("POST", "/notes")
            connection.putheader("Content-Type", "application/json")
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 411)
            response.read()
        finally:
            connection.close()
        self.assert_empty()

    def test_json_responses_declare_type_and_length(self):
        status, body, headers = self.request("GET")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"notes": []})
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertGreater(int(headers["Content-Length"]), 0)

    def test_handler_factories_do_not_share_state(self):
        self.create("Only on first server")
        other = HTTPTestCase()
        other.setUp()
        try:
            other.assert_empty()
        finally:
            other.doCleanups()

    def test_default_host_is_loopback(self):
        self.assertEqual(DEFAULT_HOST, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
