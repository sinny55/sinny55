from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .models import PropertyProfile, RevenueSnapshot
from .plan_builder import build_personalized_plan
from .pricing import monthly_recurring_revenue
from .reminders import ReminderTask, generate_monthly_reminders
from .vendor_match import Vendor, recommend_vendors


class HomeReadyService:
    """Simple in-memory app service for MVP workflows."""

    def __init__(self) -> None:
        self._profiles: dict[str, PropertyProfile] = {}

    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile = PropertyProfile(**payload)
        profile_id = str(uuid4())
        self._profiles[profile_id] = profile

        return {
            "profile_id": profile_id,
            "plan_preview": build_personalized_plan(profile)[:500],
            "tier_suggestion": self._suggest_tier(profile),
        }

    def get_plan(self, profile_id: str) -> str:
        profile = self._require_profile(profile_id)
        return build_personalized_plan(profile)

    def get_reminders(self, profile_id: str, months: int = 3) -> list[dict[str, Any]]:
        profile = self._require_profile(profile_id)
        tasks = generate_monthly_reminders(profile, date.today(), months=months)
        return [self._serialize_task(task) for task in tasks]

    def estimate_revenue(self, payload: dict[str, Any]) -> dict[str, int]:
        snapshot = RevenueSnapshot(**payload)
        return {"mrr": monthly_recurring_revenue(snapshot)}

    def recommend_vendors_for_request(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        county = payload["county"]
        needed_categories = set(payload["needed_categories"])
        limit = int(payload.get("limit", 5))

        vendors = [
            Vendor(
                name=v["name"],
                county=v["county"],
                categories=set(v["categories"]),
                sponsored=bool(v.get("sponsored", False)),
            )
            for v in payload["vendors"]
        ]
        recommended = recommend_vendors(vendors, county, needed_categories, limit)
        return [asdict(v) for v in recommended]

    def _require_profile(self, profile_id: str) -> PropertyProfile:
        if profile_id not in self._profiles:
            raise KeyError(f"Unknown profile_id: {profile_id}")
        return self._profiles[profile_id]

    @staticmethod
    def _suggest_tier(profile: PropertyProfile) -> str:
        if profile.occupancy_status == "seasonal":
            return "snowbird"
        if profile.occupancy_status == "rental" or profile.property_type == "airbnb":
            return "manager"
        return "homeowner"

    @staticmethod
    def _serialize_task(task: ReminderTask) -> dict[str, Any]:
        return {
            "due_date": task.due_date.isoformat(),
            "title": task.title,
            "channel": task.channel,
        }


class HomeReadyRequestHandler(BaseHTTPRequestHandler):
    service = HomeReadyService()
    _profile_plan_pattern = re.compile(r"^/api/profiles/([^/]+)/plan$")
    _profile_reminders_pattern = re.compile(r"^/api/profiles/([^/]+)/reminders$")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._write_html(HTTPStatus.OK, self._landing_page())
            return
        if parsed.path == "/health":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
            return

        plan_match = self._profile_plan_pattern.match(parsed.path)
        if plan_match:
            profile_id = plan_match.group(1)
            try:
                plan = self.service.get_plan(profile_id)
                self._write_json(HTTPStatus.OK, {"profile_id": profile_id, "plan": plan})
            except KeyError as exc:
                self._write_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return

        reminders_match = self._profile_reminders_pattern.match(parsed.path)
        if reminders_match:
            profile_id = reminders_match.group(1)
            months = int(parse_qs(parsed.query).get("months", ["3"])[0])
            try:
                reminders = self.service.get_reminders(profile_id, months=months)
                self._write_json(HTTPStatus.OK, {"profile_id": profile_id, "reminders": reminders})
            except KeyError as exc:
                self._write_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        payload = self._read_json_body()
        if payload is None:
            return

        try:
            if parsed.path == "/api/profiles":
                response = self.service.create_profile(payload)
                self._write_json(HTTPStatus.CREATED, response)
                return

            if parsed.path == "/api/revenue/estimate":
                response = self.service.estimate_revenue(payload)
                self._write_json(HTTPStatus.OK, response)
                return

            if parsed.path == "/api/vendors/recommend":
                response = self.service.recommend_vendors_for_request(payload)
                self._write_json(HTTPStatus.OK, {"recommendations": response})
                return

            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
        except (KeyError, TypeError, ValueError) as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid payload: {exc}"})

    def _read_json_body(self) -> dict[str, Any] | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Body must be valid JSON"})
            return None

        if not isinstance(payload, dict):
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be an object"})
            return None
        return payload

    def _write_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _write_html(self, status: HTTPStatus, html: str) -> None:
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def _landing_page() -> str:
        return """<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width,initial-scale=1' />
  <title>HomeReady Florida MVP</title>
</head>
<body>
  <h1>HomeReady Florida MVP</h1>
  <p>Core API endpoints:</p>
  <ul>
    <li>POST /api/profiles</li>
    <li>GET /api/profiles/{profile_id}/plan</li>
    <li>GET /api/profiles/{profile_id}/reminders?months=3</li>
    <li>POST /api/revenue/estimate</li>
    <li>POST /api/vendors/recommend</li>
  </ul>
  <p>Health check: <code>/health</code></p>
</body>
</html>
"""


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), HomeReadyRequestHandler)
    print(f"HomeReady Florida MVP running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
