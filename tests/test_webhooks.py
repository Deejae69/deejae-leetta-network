from __future__ import annotations

import http.server
import json
import socketserver
import threading
import unittest

from deejae.config import WebhookConfig
from deejae.webhooks import WebhookClient


class _Handler(http.server.BaseHTTPRequestHandler):
    received: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length).decode("utf-8")
        self.__class__.received.append(json.loads(raw))
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # silence
        return


class TestWebhooks(unittest.IsolatedAsyncioTestCase):
    async def test_send_event_posts_json(self) -> None:
        _Handler.received = []
        with socketserver.TCPServer(("127.0.0.1", 0), _Handler) as httpd:
            port = httpd.server_address[1]
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                client = WebhookClient(
                    WebhookConfig(default_url=f"http://127.0.0.1:{port}/", timeout_seconds=2, max_retries=0)
                )
                await client.send_event(event="test", title="t", body="b", agent_id="a1")
            finally:
                httpd.shutdown()
                httpd.server_close()

        self.assertEqual(len(_Handler.received), 1)
        self.assertEqual(_Handler.received[0]["event"], "test")
        self.assertEqual(_Handler.received[0]["agent_id"], "a1")


if __name__ == "__main__":
    unittest.main()

