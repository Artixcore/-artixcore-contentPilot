"""In-memory background job manager."""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from core.error_handler import handle_exception
from core.logging_config import get_logger

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cp-job")
_LOCK = threading.Lock()
_JOBS: dict[str, "Job"] = {}


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    result: Any = None
    error: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def _update_job(job_id: str, **kwargs) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        for k, v in kwargs.items():
            setattr(job, k, v)
        job.updated_at = datetime.now(timezone.utc)


def submit_job(job_type: str, fn: Callable[..., Any], *args, **kwargs) -> str:
    """Submit a background job and return job_id."""
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, job_type=job_type)
    with _LOCK:
        _JOBS[job_id] = job

    def _run() -> None:
        _update_job(job_id, status=JobStatus.RUNNING, progress=0.1)
        try:
            result = fn(*args, **kwargs)
            _update_job(job_id, status=JobStatus.COMPLETED, progress=1.0, result=result)
            logger.info("Job completed: id=%s type=%s", job_id, job_type)
        except Exception as exc:
            err = handle_exception(exc, context=f"job:{job_type}")
            _update_job(job_id, status=JobStatus.FAILED, error=err, progress=1.0)
            logger.error("Job failed: id=%s type=%s", job_id, job_type)

    _executor.submit(_run)
    return job_id


def get_job(job_id: str) -> Job | None:
    with _LOCK:
        return _JOBS.get(job_id)


def list_jobs(job_type: str | None = None) -> list[Job]:
    with _LOCK:
        jobs = list(_JOBS.values())
    if job_type:
        jobs = [j for j in jobs if j.job_type == job_type]
    return sorted(jobs, key=lambda j: j.created_at, reverse=True)


def reset_jobs() -> None:
    with _LOCK:
        _JOBS.clear()
