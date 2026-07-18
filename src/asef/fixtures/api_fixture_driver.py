from __future__ import annotations

import http.client
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            payload, status = {"status": "ok", "service": "asef-sandbox-fixture"}, 200
        else:
            payload, status = {"error": "not-found"}, 404
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        return


def contains_subset(observed, expected) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(
            key in observed and contains_subset(observed[key], value) for key, value in expected.items()
        )
    return observed == expected


def main() -> int:
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    origin = urlsplit(plan["base_url"])
    if origin.hostname != "127.0.0.1" or origin.port is None:
        return 2
    server = ThreadingHTTPServer(("127.0.0.1", origin.port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    try:
        for scenario in plan["scenarios"]:
            started = time.monotonic()
            connection = http.client.HTTPConnection("127.0.0.1", origin.port, timeout=5)
            try:
                connection.request(scenario["method"], scenario["path"])
                response = connection.getresponse()
                content = response.read(1_048_577)
                diagnostic = None
                status = "PASSED"
                if response.status != scenario["assertion"]["expected_status"]:
                    status, diagnostic = "FAILED", "STATUS_MISMATCH"
                elif "expected_json_subset" in scenario["assertion"]:
                    try:
                        observed = json.loads(content.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        status, diagnostic = "FAILED", "INVALID_JSON_RESPONSE"
                    else:
                        if not contains_subset(observed, scenario["assertion"]["expected_json_subset"]):
                            status, diagnostic = "FAILED", "JSON_SUBSET_MISMATCH"
                results.append(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "status": status,
                        "observed_status": response.status,
                        "duration_ms": max(0, round((time.monotonic() - started) * 1000)),
                        "response_bytes": len(content),
                        "diagnostic_code": diagnostic,
                    }
                )
            finally:
                connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    passed = sum(item["status"] == "PASSED" for item in results)
    failed = sum(item["status"] == "FAILED" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)
    payload = {
        "schema_version": "1.0.0",
        "plan_id": plan["plan_id"],
        "status": "ERROR" if errors else ("FAILED" if failed else "PASSED"),
        "tests": len(results),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "scenarios": results,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
