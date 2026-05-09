from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from api.grading_api import grade_text_payload
from config.env import load_env
from line.signature_guard import is_valid_line_signature
from line.webhook import handle_webhook_body
from utils.logger import logger


class ChattieHandler(BaseHTTPRequestHandler):
    server_version = "ChattiePy/0.1"

    def _read_json(self) -> tuple[bytes, dict[str, Any] | None]:
        length = int(self.headers.get("content-length", "0") or "0")
        body = self.rfile.read(length) if length else b""
        if not body:
            return body, None
        try:
            return body, json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return body, None

    def _send_text(self, status: int, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_text(200, "OK")
            return
        self._send_text(404, "Not Found")

    def do_POST(self) -> None:
        body, payload = self._read_json()

        if self.path == "/grade":
            status, response = grade_text_payload(payload)
            self._send_json(status, response)
            return

        if self.path == "/callback":
            signature = self.headers.get("x-line-signature")
            if not is_valid_line_signature(body, signature):
                self._send_text(401, "Missing or invalid LINE signature")
                return
            self._send_text(200, "OK")
            try:
                handle_webhook_body(payload or {})
            except Exception as exc:
                logger.error("callback handling failed: %s", exc)
            return

        self._send_text(404, "Not Found")

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)


def main() -> None:
    env = load_env(require_credentials=False)
    server = ThreadingHTTPServer(("0.0.0.0", env.port), ChattieHandler)
    logger.info("Server running on port %s", env.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
