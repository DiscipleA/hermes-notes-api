"""Tiny loopback-only, in-memory notes API using the Python standard library."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlsplit

DEFAULT_HOST = "127.0.0.1"
MAX_BODY_BYTES = 16_384


def make_handler():
    """Create an independent notes store and its HTTP request handler class."""
    notes = {}
    next_id = 1

    class NotesHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Avoid logging note contents or noisy requests in the classroom demo.
            pass

        def respond(self, status, body=None):
            content = b"" if body is None else json.dumps(body).encode("utf-8")
            self.send_response(status)
            if body is not None:
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if content:
                self.wfile.write(content)

        def error(self, status, message):
            self.respond(status, {"error": message})

        def do_GET(self):
            if urlsplit(self.path).path != "/notes":
                return self.error(404, "Not found")
            self.respond(200, {"notes": list(notes.values())})

        def do_POST(self):
            nonlocal next_id
            if urlsplit(self.path).path != "/notes":
                return self.error(404, "Not found")
            lengths = self.headers.get_all("Content-Length", [])
            if not lengths:
                return self.error(411, "Content-Length required")
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                return self.error(400, "Invalid Content-Length")
            # Compare before conversion so very long decimal headers are bounded too.
            length_text = lengths[0].lstrip("0") or "0"
            maximum = str(MAX_BODY_BYTES)
            if len(length_text) > len(maximum) or (
                len(length_text) == len(maximum) and length_text > maximum
            ):
                return self.error(413, "Request body too large")
            length = int(length_text)
            if self.headers.get_content_type() != "application/json":
                return self.error(415, "Content-Type must be application/json")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, ValueError, RecursionError):
                return self.error(400, "Malformed JSON body")
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not text or not text.strip():
                return self.error(400, "text must be a non-empty string")
            note = {"id": next_id, "text": text}
            notes[next_id] = note
            next_id += 1
            self.respond(201, note)

        def do_DELETE(self):
            path = urlsplit(self.path).path
            parts = path.split("/")
            if len(parts) != 3 or parts[1] != "notes" or not parts[2].isascii() or not parts[2].isdecimal():
                return self.error(404, "Not found")
            # Canonical identifiers avoid unbounded integer conversions on user input.
            if len(parts[2]) > 12:
                return self.error(404, "Not found")
            note_id = int(parts[2])
            if note_id not in notes:
                return self.error(404, "Note not found")
            del notes[note_id]
            self.respond(204)

    return NotesHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="Loopback port (default: 8000; 0 picks a free port)")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    with HTTPServer((DEFAULT_HOST, args.port), make_handler()) as server:
        print(f"Listening on http://{DEFAULT_HOST}:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
