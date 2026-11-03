"""Copy to repo/tests/test_regression.py for the intentionally RED bug-fix PR."""
import unittest

from tests.http_case import HTTPTestCase


class WhitespaceRegressionTests(HTTPTestCase):
    def test_whitespace_only_text_is_rejected_without_mutation(self):
        existing = self.create("Existing note")
        status, _, _ = self.request("POST", payload={"text": " \t\r\n "})
        list_status, body, _ = self.request("GET")
        self.assertEqual(
            (status, list_status, body),
            (400, 200, {"notes": [existing]}),
            "Whitespace-only text must return 400 and leave existing notes unchanged",
        )

    def test_nonblank_text_keeps_its_original_whitespace(self):
        text = "  Keep my spacing\n"
        note = self.create(text)
        self.assertEqual(note["text"], text)
        self.assertEqual(self.request("GET")[1], {"notes": [note]})


if __name__ == "__main__":
    unittest.main()
