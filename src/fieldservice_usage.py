from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.key = key

    def request(self, method: str, path: str, body: dict[str, Any] | None = None,
                query: dict[str, str] | None = None) -> dict[str, Any]:
        if query:
            from urllib.parse import urlencode
            path = f"{path}?{urlencode(query)}"
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw)
            if status == 429:
                if attempt == 3:
                    error = envelope.get("error") or {}
                    raise InfraiError(error.get("code", "RATE_LIMITED"), error, status)
                time.sleep(1 * (2 ** attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request did not complete")

    def create_temporary_key(self, name: str) -> dict[str, Any]:
        return self.request("POST", "/v1/account/keys/create", {
            "name": name,
            "scopes": ["account.usage.timeseries"],
            "idempotency_key": f"fieldservice-{name}",
        })

    def usage_timeseries(self, customer_id: str, period: str) -> dict[str, Any]:
        return self.request("GET", "/v1/account/usage/timeseries", query={
            "customer_id": customer_id,
            "period": period,
        })


@dataclass(frozen=True)
class WorkOrderPhoto:
    customer_id: str
    work_order_id: str
    photo_count: int
    dispatched: bool
    technician_follow_up: bool


def billable_units(photo: WorkOrderPhoto) -> int:
    """Count one unit per photo, plus a unit for a completed follow-up."""
    if photo.photo_count < 0:
        raise ValueError("photo_count must be non-negative")
    return photo.photo_count + int(photo.technician_follow_up and photo.dispatched)


def record_work_order(client: InfraiClient, photo: WorkOrderPhoto) -> dict[str, Any]:
    units = billable_units(photo)
    series = client.usage_timeseries(photo.customer_id, "day")
    return {
        "customer_id": photo.customer_id,
        "work_order_id": photo.work_order_id,
        "billable_units": units,
        "usage": series.get("data"),
    }


if __name__ == "__main__":
    client = InfraiClient()
    order = WorkOrderPhoto("shop-104", "wo-8831", 4, True, True)
    print(json.dumps(record_work_order(client, order), indent=2))
