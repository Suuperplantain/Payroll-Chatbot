from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.payroll_support import (
    AuthService,
    InMemoryKnowledgeRepository,
    InMemoryMetricsRepository,
    InMemoryPayrollRepository,
    InMemoryTicketRepository,
    PayrollSupportService,
    RuleBasedNLPEngine,
)

WEB_DIR = Path(__file__).parent / "web"

auth_service = AuthService(
    allowed_employee_ids={"E1001", "E1002"},
    token_to_employee_id={
        "token-E1001": "E1001",
        "token-E1002": "E1002",
    },
)
metrics_repo = InMemoryMetricsRepository()

service = PayrollSupportService(
    auth_service=auth_service,
    nlp_engine=RuleBasedNLPEngine(),
    knowledge_repo=InMemoryKnowledgeRepository(),
    payroll_repo=InMemoryPayrollRepository(),
    ticket_repo=InMemoryTicketRepository(),
    metrics_repo=metrics_repo,
)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        payload_raw = self.rfile.read(content_length)
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc

        if not isinstance(payload, dict):
            raise ValueError("JSON payload must be an object")
        return payload

    def _validate_auth(self, payload: dict) -> str | None:
        employee_id = payload.get("employee_id")
        token = payload.get("token")
        employee_id_str = str(employee_id) if employee_id is not None else None
        token_str = str(token) if token is not None else None
        return auth_service.validate_credentials(employee_id=employee_id_str, token=token_str)

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/api/health":
                self._json_response(HTTPStatus.OK, {"status": "ok"})
                return

            if self.path == "/api/metrics":
                summary = metrics_repo.get_summary()
                self._json_response(
                    HTTPStatus.OK,
                    {
                        "total_interactions": summary.total_interactions,
                        "deflection_rate": round(summary.deflection_rate, 4),
                        "average_response_time": round(summary.average_response_time, 4),
                        "error_rate": round(summary.error_rate, 4),
                        "handoff_rate": round(summary.handoff_rate, 4),
                    },
                )
                return

            super().do_GET()
        except Exception:
            self._json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Internal server error"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/api/chat":
                self._handle_chat()
                return

            if self.path in {"/api/update-address", "/api/update-bank"}:
                self._handle_hr_update_request()
                return

            self._json_response(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except ValueError as exc:
            self._json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception:
            self._json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Internal server error"})

    def _handle_chat(self) -> None:
        payload = self._read_json_body()
        employee_id = self._validate_auth(payload)
        message = payload.get("message")

        if employee_id is None:
            metrics_repo.record_interaction(outcome="error", response_time=0.0)
            self._json_response(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"})
            return

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Invalid request body")

        result = service.handle_message(employee_id=employee_id, message=message)
        self._json_response(
            HTTPStatus.OK,
            {
                "status": result.status,
                "message": result.message,
                "route": result.route,
                "payslip_summary": result.payslip_summary,
            },
        )

    def _handle_hr_update_request(self) -> None:
        payload = self._read_json_body()
        employee_id = self._validate_auth(payload)

        if employee_id is None:
            metrics_repo.record_interaction(outcome="error", response_time=0.0)
            self._json_response(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"})
            return

        print(f"Received {self.path} request for {employee_id}: {payload}")
        metrics_repo.record_interaction(outcome="automated", response_time=0.0)
        self._json_response(
            HTTPStatus.OK,
            {
                "status": "ok",
                "message": "Request received and logged. HR will process this update.",
            },
        )


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Payroll pilot app running at http://localhost:8000")
    server.serve_forever()
