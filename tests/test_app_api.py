import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import app


class AppApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        app.metrics_repo._events.clear()  # type: ignore[attr-defined]

    def _post(self, path: str, payload: dict) -> tuple[int, dict]:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as response:
                body = json.loads(response.read().decode("utf-8"))
                return response.status, body
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            return exc.code, body

    def _get(self, path: str) -> tuple[int, dict]:
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method="GET")
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body

    def test_chat_requires_auth(self) -> None:
        status, body = self._post("/api/chat", {"employee_id": "BAD", "message": "tax"})
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "Unauthorized")

    def test_chat_returns_payslip_summary(self) -> None:
        status, body = self._post(
            "/api/chat",
            {"employee_id": "E1001", "message": "show my payslip"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["route"], "payroll")
        self.assertIn("payslip_summary", body)
        self.assertEqual(body["payslip_summary"]["net_pay"], 4250.35)

    def test_update_address_endpoint(self) -> None:
        status, body = self._post(
            "/api/update-address",
            {
                "employee_id": "E1001",
                "address_line_1": "10 Test Street",
                "city": "London",
                "postcode": "SW1A 1AA",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_metrics_endpoint(self) -> None:
        self._post("/api/chat", {"employee_id": "E1001", "message": "How is my tax calculated?"})
        self._post("/api/chat", {"employee_id": "E1001", "message": "I have a unique situation"})
        self._post("/api/chat", {"employee_id": "BAD", "message": "tax"})

        status, body = self._get("/api/metrics")
        self.assertEqual(status, 200)
        self.assertEqual(body["total_interactions"], 3)
        self.assertAlmostEqual(body["deflection_rate"], 0.3333, places=4)
        self.assertAlmostEqual(body["handoff_rate"], 0.3333, places=4)
        self.assertAlmostEqual(body["error_rate"], 0.3333, places=4)


if __name__ == "__main__":
    unittest.main()
