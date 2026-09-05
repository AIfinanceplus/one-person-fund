from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.contracts.roles import ROLE_CONTRACTS
from backend.orchestration.demo import run_demo
from backend.orchestration.full_run import run_full_demo
from backend.orchestration.scenarios import run_scenario


ROOT = Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/scenarios/"):
            name = self.path.rsplit("/", 1)[-1]
            try:
                payload = run_scenario(name)
            except ValueError as exc:
                self.send_error(404, str(exc))
                return
            self._send(json.dumps(payload, default=str).encode(), "application/json; charset=utf-8")
            return
        if self.path in {"/api/full", "/api/status", "/api/strategy", "/api/portfolio", "/api/risk", "/api/orders", "/api/ledger", "/api/fundbench"}:
            result = run_full_demo()
            if self.path == "/api/status":
                payload = {"run_id": result["run_id"], "status": result["status"], "mode": "DEMO", "roles": 14, "strategy_pods": 5, "risk": result.get("artifacts", {}).get("risk_decision", {}), "human_inbox": []}
            elif self.path == "/api/strategy":
                payload = result.get("artifacts", {}).get("pods", [])
            elif self.path == "/api/portfolio":
                payload = result.get("artifacts", {}).get("portfolio", {})
            elif self.path == "/api/risk":
                payload = result.get("artifacts", {}).get("risk_decision", {})
            elif self.path == "/api/orders":
                payload = result.get("artifacts", {}).get("fills", [])
            elif self.path == "/api/ledger":
                payload = result.get("artifacts", {}).get("ledger", {})
            elif self.path == "/api/fundbench":
                payload = result.get("artifacts", {}).get("fundbench", {})
            else:
                payload = result
            self._send(json.dumps(payload, default=str).encode(), "application/json; charset=utf-8")
            return
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
