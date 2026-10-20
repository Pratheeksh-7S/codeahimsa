"""Tiny HTTP client for a local `strands-decider serve` server."""

import os
import time

import httpx

DEFAULT_URL = os.environ.get("STRANDS_DECIDER_URL", "http://127.0.0.1:8099")


class DeciderClient:
    def __init__(self, url: str = DEFAULT_URL, timeout: float = 60.0):
        self._url = url.rstrip("/") + "/v1/systemone"
        self._http = httpx.Client(timeout=timeout)

    def ask(self, state: str, questions: dict) -> tuple[dict, float]:
        """Return ({question_name: answer_dict}, round-trip latency in ms)."""
        start = time.perf_counter()
        resp = self._http.post(self._url, json={"state": state, "questions": questions})
        resp.raise_for_status()
        latency_ms = (time.perf_counter() - start) * 1000
        return resp.json()["answers"], latency_ms
