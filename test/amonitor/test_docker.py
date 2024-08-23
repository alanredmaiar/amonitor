import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import tempfile

import pytest

from amonitor.docker import DockerMonitor, aget_containers


class MockDocker:
    def __init__(self, url=None):
        self.containers = []

    async def __aenter__(self):
        return self



@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filter_name, filter_port, mock_containers, expected_result",
    [
        (None, None, [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}], [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}]),
        ("test", None, [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}], [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}]),
        ("not_in_list", None, [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}], []),
        (None, 8080, [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}], [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}]),
        (None, 9999, [{"Names": ["/test_container_1"], "Ports": [{"PublicPort": 8080}]}], []),
    ],
)
async def test_aget_containers(filter_name, filter_port, mock_containers, expected_result):
    lister = AsyncMock(return_value=mock_containers)
    with patch("aiodocker.containers.DockerContainers.list", new=lister) as mock_list:
        result = await aget_containers(filter_name=filter_name, filter_port=filter_port)
        mock_list.assert_called_once()
        assert len(result) == len(expected_result)


@pytest.mark.asyncio
async def test_docker_monitor(docker_stats_stream, docker_logs_stream):
    host = "unix:///home/user/.docker/desktop/docker.sock"
    n_samples = 3
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        docker_monitor = DockerMonitor(host=host)

        # Mocking Docker client behavior
        docker_monitor.client.containers.list = AsyncMock(return_value=[{"Names": ["/main_container"]}])
        container_mock = AsyncMock()
        container_mock.stats = docker_stats_stream
        container_mock.log = docker_logs_stream
        docker_monitor.client.containers.get = AsyncMock(return_value=container_mock)
        
        async with docker_monitor.monitor(container_name="main_container") as monitor:
            await asyncio.sleep(n_samples)

        summary = await monitor.summarize()
        assert summary is not None
        assert 'cpu' in summary
        assert 'memory' in summary
        assert 'disk_read' in summary
        assert round(summary["latency"]) == 1

        # Test data saving
        basepath = await docker_monitor.save(basepath=data_dir, prefix="test")
        summary_path = (basepath / "summary.csv")
        stats_path = (basepath / "stats.csv")
        assert summary_path.exists()
        assert stats_path.exists()

        # Clean up after test
        summary_path.unlink()
        stats_path.unlink()


