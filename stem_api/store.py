from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobStore:
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)

    def create(self, job_id: str, payload: dict[str, Any]) -> None:
        self.jobs[job_id] = payload

    def get(self, job_id: str) -> dict[str, Any]:
        return self.jobs[job_id]

    def exists(self, job_id: str) -> bool:
        return job_id in self.jobs

    def delete(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)

    def status_map(self) -> dict[str, str]:
        return {job_id: payload.get("status", "unknown") for job_id, payload in self.jobs.items()}


job_store = JobStore()
