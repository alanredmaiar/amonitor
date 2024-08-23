import asyncio
import pytest
import time
import multiprocessing
from typing import Generator, Any

from unittest.mock import MagicMock


@pytest.fixture
def stress_cpu(seconds=3, load_cores=2):
    """
    Increase CPU usage by spinning up processes that do busy work.
    """
    def busy_work():
        end_time = time.time() + seconds
        while time.time() < end_time:
            pass

    processes = []
    for _ in range(load_cores):
        p = multiprocessing.Process(target=busy_work)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


@pytest.fixture
def allocate_memory(size_in_mb=500):
    """
    Allocate a large amount of memory (dummy data) to simulate high memory usage.
    """
    large_list = [0] * (size_in_mb * 1024 * 1024 // 8)  # Allocate list of large size
    time.sleep(3)  # Hold the memory for a few seconds
    return large_list


@pytest.fixture
def docker_stats() -> list[dict]:
    """Fixture to provide simulated Docker stats data."""
    return [
        {'read': '2024-05-13T15:23:12.266228192Z', 'preread': '2024-05-13T15:23:11.26130696Z', 'pids_stats': {'current': 5, 'limit': 18446744073709551615}, 'blkio_stats': {'io_service_bytes_recursive': [{'major': 254, 'minor': 0, 'op': 'read', 'value': 0}, {'major': 254, 'minor': 0, 'op': 'write', 'value': 45056}]}, 'cpu_stats': {'cpu_usage': {'total_usage': 31904710000}, 'system_cpu_usage': 641055550000000, 'online_cpus': 20}, 'memory_stats': {'usage': 106971136, 'limit': 41266020352}, 'networks': {'eth0': {'rx_bytes': 2997560, 'tx_bytes': 967312}}},
        {'read': '2024-05-13T15:23:13.270733311Z', 'preread': '2024-05-13T15:23:12.266228192Z', 'pids_stats': {'current': 5, 'limit': 18446744073709551615}, 'blkio_stats': {'io_service_bytes_recursive': [{'major': 254, 'minor': 0, 'op': 'read', 'value': 0}, {'major': 254, 'minor': 0, 'op': 'write', 'value': 45056}]}, 'cpu_stats': {'cpu_usage': {'total_usage': 31907563000}, 'system_cpu_usage': 641075550000000, 'online_cpus': 20}, 'memory_stats': {'usage': 107229184, 'limit': 41266020352}, 'networks': {'eth0': {'rx_bytes': 2997696, 'tx_bytes': 967452}}}
    ]

@pytest.fixture
def docker_stats_stream(docker_stats) -> Generator[Any, None, Any]:
    """Fixture to provide simulated Docker stats data."""
    
    async def stats_stream(stats_data):
        """An asynchronous generator that yields Docker stats."""
        for stat in stats_data:
            yield stat
            await asyncio.sleep(0.1)

    yield MagicMock(side_effect=lambda stream=True: stats_stream(docker_stats))

@pytest.fixture
def docker_logs() -> list[str]:
    """Fixture to provide simulated Docker logs data."""
    return [
        '2024-05-13T15:23:12.266228192Z [INFO] Starting server...',
        '2024-05-13T15:23:13.270733311Z [ERROR] Connection refused'
    ]

@pytest.fixture
def docker_logs_stream(docker_logs) -> Generator[Any, None, Any]:
    """Fixture to provide simulated Docker logs data."""
    
    async def logs_stream(logs_data):
        """An asynchronous generator that yields Docker logs."""
        for log in logs_data:
            yield log
            await asyncio.sleep(0.1)

    yield MagicMock(side_effect=lambda stdout, stderr, follow, since=True: logs_stream(docker_logs))
