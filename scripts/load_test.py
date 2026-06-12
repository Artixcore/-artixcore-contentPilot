#!/usr/bin/env python3
"""Basic local stress test for ContentPilot reliability layer."""

from __future__ import annotations

import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from core.cache import clear_cache, get_or_set
from core.database import check_database_health, init_db, reset_engine
from core.health import run_health_checks
from core.rate_limiter import reset_rate_limits


ENABLE_REAL_API = os.getenv("ENABLE_REAL_API_LOAD_TEST", "false").lower() in ("true", "1", "yes")
ITERATIONS = int(os.getenv("LOAD_TEST_ITERATIONS", "50"))
WORKERS = int(os.getenv("LOAD_TEST_WORKERS", "10"))


def _run_health():
    start = time.perf_counter()
    run_health_checks()
    return time.perf_counter() - start


def _run_db_check():
    start = time.perf_counter()
    reset_engine("sqlite:///:memory:")
    init_db()
    check_database_health()
    return time.perf_counter() - start


def _run_cache():
    start = time.perf_counter()
    clear_cache()
    get_or_set("load_test", lambda: {"ok": True}, ttl=5)
    return time.perf_counter() - start


def _run_validation():
    from core.schemas import Platform

    start = time.perf_counter()
    Platform("linkedin")
    return time.perf_counter() - start


TASKS = {
    "health_checks": _run_health,
    "database_reads": _run_db_check,
    "cache_ops": _run_cache,
    "validation": _run_validation,
}


def main() -> int:
    print("ContentPilot Load Test")
    print(f"  iterations={ITERATIONS} workers={WORKERS} real_api={ENABLE_REAL_API}")
    reset_rate_limits()

    latencies: list[float] = []
    errors: list[str] = []
    success = 0
    failure = 0

    task_names = list(TASKS.keys())

    def _task(i: int) -> float:
        fn = TASKS[task_names[i % len(task_names)]]
        return fn()

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_task, i) for i in range(ITERATIONS)]
        for fut in as_completed(futures):
            try:
                latencies.append(fut.result())
                success += 1
            except Exception as exc:
                failure += 1
                errors.append(type(exc).__name__)

    print(f"\nResults:")
    print(f"  success: {success}")
    print(f"  failure: {failure}")
    if latencies:
        print(f"  avg latency: {statistics.mean(latencies)*1000:.1f}ms")
        print(f"  max latency: {max(latencies)*1000:.1f}ms")
    if errors:
        print(f"  errors: {', '.join(sorted(set(errors)))}")
    return 0 if failure == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
