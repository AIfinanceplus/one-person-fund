from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.contracts.roles import ROLE_CONTRACTS
from backend.orchestration.demo import run_demo


ROOT = Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/demo":
            self._send(json.dumps(run_demo(), default=str).encode(), "application/json; charset=utf-8")
            return
        if self.path == "/api/roles":
            self._send(json.dumps([role.__dict__ for role in ROLE_CONTRACTS]).encode(), "application/json; charset=utf-8")
            return
        page = (ROOT / "frontend" / "index.html").read_bytes()
        self._send(page, "text/html; charset=utf-8")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Rates Fund OS listening at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
