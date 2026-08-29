"""
Hand-rolled stress test: fires concurrent requests at a target URL and reports
throughput + latency stats.

Usage:
    python scripts/stress_test.py --url http://127.0.0.1:8000/<short_code> \
        --requests 500 --concurrency 50
"""

import argparse
import asyncio
import statistics
import time

import httpx


async def fire_one(client: httpx.AsyncClient, url: str) -> tuple[float, int]:
    start = time.perf_counter()
    try:
        response = await client.get(url, follow_redirects=False)
        status = response.status_code
    except Exception:
        status = -1
    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms, status


def percentile(sorted_values: list[float], p: float) -> float:
    idx = max(int(len(sorted_values) * p) - 1, 0)
    return sorted_values[idx]


async def run(url: str, total_requests: int, concurrency: int) -> None:
    latencies: list[float] = []
    statuses: list[int] = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bound_fire(client: httpx.AsyncClient) -> None:
        async with semaphore:
            latency, status = await fire_one(client, url)
            latencies.append(latency)
            statuses.append(status)

    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.perf_counter()
        await asyncio.gather(*[bound_fire(client) for _ in range(total_requests)])
        total_time = time.perf_counter() - start

    successes = sum(1 for s in statuses if 200 <= s < 400)
    failures = total_requests - successes
    latencies.sort()

    print(f"Target: {url}")
    print(f"Total requests: {total_requests} (concurrency={concurrency})")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {total_requests / total_time:.1f} req/s")
    print(f"Successes: {successes}  Failures: {failures}")
    print(
        f"Latency (ms): min={min(latencies):.1f} avg={statistics.mean(latencies):.1f} "
        f"p50={percentile(latencies, 0.50):.1f} p95={percentile(latencies, 0.95):.1f} "
        f"p99={percentile(latencies, 0.99):.1f} max={max(latencies):.1f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand-rolled stress test")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    asyncio.run(run(args.url, args.requests, args.concurrency))


if __name__ == "__main__":
    main()
