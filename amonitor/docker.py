import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
import logging
from typing import Literal
from datetime import datetime

from aiodocker import Docker
from aiodocker.containers import DockerContainer
from aiodocker.exceptions import DockerError, DockerContainerError
import pandas as pd

from .utils import to_timestamp, safe_path



async def aget_containers(filter_name: str | None = None, filter_port: int | None = None):
    """Returns a list of existing containers with optional filtering by name or port."""
    try:
        host = os.getenv("DOCKER_HOST")
        client = Docker(host) if host else Docker()
        containers = await client.containers.list()
        if filter_name:
            containers = [c for c in containers if filter_name.lower() in c['Names'][0].lower()]
        if filter_port:
            containers = [c for c in containers if any(filter_port == port.get('PublicPort') or filter_port == port.get('PrivatePort') for port in c['Ports'])]
        return containers
    except Exception as e:
        print(f"Failed to retrieve containers: {e}")
        return []



class DockerMonitor:
    """Class to monitor Docker container resources asynchronously."""

    def __init__(self, host: str | None = os.getenv("DOCKER_HOST"), container_name: str | None = None):
        self.client = Docker(host) if host else Docker()
        self._num_cores: int = 1
        self.raw_stats: list[dict[str, float]] = []
        self.transformed_stats: list[dict[str, float]] = []
        self._aggregated_stats: dict[str, list[float]] = {}
        self._summary: dict[str, dict[str, float] | float | int] = {}
        self._logs: list[str] = []
        self.container_name = container_name

    @property
    def summary(self):
        return self._summary
    
    @property
    def logs(self):
        return self._logs
    
    @property
    def aggregated_stats(self):
        return self._aggregated_stats

    async def list_containers(self):
        """List all running containers."""
        try:
            containers = await self.client.containers.list()
            return [c['Names'][0].lstrip('/') for c in containers]
        except Exception as e:
            raise ValueError(f"Error fetching container list: {str(e)}")

    async def get_container(self, container_name):
        """Get a specific container by name."""
        try:
            container = await self.client.containers.get(container_name)
            return container
        except (DockerError, DockerContainerError, ) as ex:
            logging.error(f"Error fetching container {container_name}: {ex}")
            raise ex

    @staticmethod
    def _calculate_metrics(data: list[float]) -> dict[str, float]:
        """Calculates min, max, and average from a list of data."""
        if not data:
            return {"min": 0, "max": 0, "avg": 0}
        return {
            "min": min(data) if data else 0,
            "max": max(data) if data else 0,
            "avg": (sum(data) / len(data)) if data else 0
        }

    @staticmethod
    async def _calculate_timestamp(raw_stat: dict) -> int:
        """Calculates timestamps from the raw stats."""
        return to_timestamp(raw_stat['read'])
    
    @staticmethod
    async def _calculate_cpu(raw_stat: dict) -> tuple[float, float]:
        """Calculates CPU usage statistics."""
        cpu_percent = num_cpus = 0
        
        cpu_usage = raw_stat.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) or 0
        precpu_usage = raw_stat.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) or 0
        cpu_usage_delta = cpu_usage - precpu_usage

        system_cpu = raw_stat.get('cpu_stats', {}).get('system_cpu_usage', 0) or 0
        presystem_cpu = raw_stat.get('precpu_stats', {}).get('system_cpu_usage', 0) or 0
        system_cpu_delta = system_cpu - presystem_cpu

        num_cpus = raw_stat.get('cpu_stats', {}).get('online_cpus', 1) or 1
        if system_cpu_delta > 0:
            cpu_percent = (cpu_usage_delta / system_cpu_delta) * num_cpus * 100  # type: ignore

        return cpu_percent, num_cpus

    @staticmethod
    async def _calculate_memory(raw_stat: dict) -> tuple[float, float]:
        """Calculates memory usage statistics."""
        mem_usage_mb = raw_stat["memory_stats"]["usage"] / (1024**2)
        total_mem_mb = raw_stat["memory_stats"]["limit"] / (1024**2)
        return mem_usage_mb, total_mem_mb

    @staticmethod
    async def _calculate_network(raw_stat: dict) -> tuple[float, float]:
        """Calculates network read and write statistics."""
        eth0 = raw_stat.get('networks', {}).get('eth0', {})
        rx_byte = eth0.get('rx_bytes', 0) / 1048576
        tx_byte = eth0.get('tx_bytes', 0) / 1048576
        return rx_byte, tx_byte

    @staticmethod
    async def _calculate_disk(raw_stat: dict) -> tuple[float, float]:
        """Calculates disk read and write statistics in megabytes."""
        io_service_bytes = raw_stat.get('blkio_stats', {}).get('io_service_bytes_recursive', [])
        read_bytes = write_bytes = 0
        
        if io_service_bytes:
            for entry in io_service_bytes:
                if entry.get('op') == 'Read':
                    read_bytes += entry.get('value', 0)
                elif entry.get('op') == 'Write':
                    write_bytes += entry.get('value', 0)

        read_mb = read_bytes / (1024**2)
        write_mb = write_bytes / (1024**2)
        return read_mb, write_mb

    @staticmethod
    def filter_by_timestamp(aggregated_data: dict, ts_range: tuple[int | float, int | float]) -> dict:
        """Filter transformed data by a timestamp range."""
        start_ts, end_ts = ts_range
        if aggregated_data:
            filtered_indices = [i for i, ts in enumerate(aggregated_data['timestamp']) if start_ts <= int(ts) <= end_ts]
            filtered_data = {}
            for key, values in aggregated_data.items():
                if isinstance(values, list) and len(values) == len(aggregated_data['timestamp']):
                    filtered_data[key] = [values[i] for i in filtered_indices]
            return filtered_data
        return aggregated_data

    @classmethod
    async def transform_stats(cls, raw_stat: dict) -> dict:
        """Transforms raw data into a dictionary of lists."""
        (
            timestamp,
            (cpu_usages, num_cores),
            (memory_usages, total_memory),
            (
                network_usages_read,
                network_usages_write,
            ),
            (
                disk_usages_read,
                disk_usages_write,
            ),
        ) = await asyncio.gather(
            cls._calculate_timestamp(raw_stat),
            cls._calculate_cpu(raw_stat),
            cls._calculate_memory(raw_stat),
            cls._calculate_network(raw_stat),
            cls._calculate_disk(raw_stat)
        )
        data = {
            "timestamp": timestamp,
            "cpu_usage": cpu_usages,
            "num_cores": num_cores,
            "memory_usage": memory_usages,
            "total_memory": total_memory,
            "network_usages_read": network_usages_read,
            "network_usages_write": network_usages_write,
            "disk_usages_read": disk_usages_read,
            "disk_usages_write": disk_usages_write,
        }
        return data

    async def aggregate_stats(self) -> dict:
        """Aggregates transformed stats into a single dictionary."""
        aggregated_stats: dict[str, list[float]] = {}
        if self.transformed_stats:
            all_keys: set = set()
            for stat in self.transformed_stats:
                all_keys.update(stat.keys())
            for key in all_keys:
                if values := [stat.get(key) for stat in self.transformed_stats]:
                    aggregated_stats[key] = values  # type: ignore
        self._aggregated_stats = aggregated_stats
        return aggregated_stats

    async def collect_data(self, container_name: str | None = None):
        """Collect Docker container stats asynchronously using an async for loop."""
        container_name = container_name or self.container_name
        container: DockerContainer = await self.get_container(container_name)
        try:
            self.raw_stats = []
            self.transformed_stats = []
            self._logs = []
            logging.info("Collecting stats for container %s", container_name)

            ts = int(datetime.now().timestamp())
            stats_stream = container.stats(stream=True)
            logs_stream = container.log(stdout=True, stderr=True, follow=True, since=ts)

            async def collect_stats():
                async for stat in stats_stream:
                    self.raw_stats.append(stat)
                    transformed_stat = await self.transform_stats(stat)
                    self.transformed_stats.append(transformed_stat)
                    logging.info(transformed_stat)

            async def collect_logs():
                async for log in logs_stream:
                    self._logs.append(log)
                    logging.info(log)

            await asyncio.gather(collect_stats(), collect_logs())
        except Exception as e:
            logging.error(f"Error collecting data for container {container_name}: {e}")
            raise ValueError(f"Error collecting data for container {container_name}: {e}")

    @asynccontextmanager
    async def monitor(self, container_name: str | None = None):
        """Context manager to start and stop resource monitoring."""
        self.task = asyncio.ensure_future(self.collect_data(container_name))
        try:
            yield self
        finally:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logging.info("Data collection task was cancelled.")
            self._aggregated_stats = await self.aggregate_stats()
            self._summary = await self.summarize()
            await self.client.close()

    async def summarize(
        self,
        ts_range: tuple[int | float, int | float] | None = None,
        fmt: Literal["dataframe", "dict"] = "dict",
        **kwargs
    ) -> pd.DataFrame | dict:
        """Calculates the summary statistics from collected data."""
        summary, agg = {}, self._aggregated_stats.copy() or await self.aggregate_stats()
        if agg and ts_range:
            agg = self.filter_by_timestamp(agg, ts_range)
        if agg:
            summary = {
                'timestamp': agg.get('timestamp', [0])[0],
                'cpu': self._calculate_metrics(agg["cpu_usage"]),
                'num_cores': agg["num_cores"][0],
                'memory': self._calculate_metrics(agg["memory_usage"]),
                'network_read': self._calculate_metrics(agg["network_usages_read"]),
                'network_write': self._calculate_metrics(agg["network_usages_write"]),
                'disk_read': self._calculate_metrics(agg["disk_usages_read"]),
                'disk_write': self._calculate_metrics(agg["disk_usages_write"]),
                'latency': agg.get('timestamp', [0])[-1] - agg.get('timestamp', [0])[0]
            }
            summary.update(kwargs)
        return summary if fmt == "dict" else pd.DataFrame(summary)

    async def export(self, ts_range: tuple[int | float, int | float] | None = None, fmt: Literal["dataframe", "dict"] = "dataframe", **kwargs) -> pd.DataFrame | list[dict]:
        """Exports the collected stats to a DataFrame."""
        agg = self._aggregated_stats.copy()
        agg.update(kwargs)
        filtered_data = self.filter_by_timestamp(agg, ts_range) if ts_range else agg
        df = pd.DataFrame(filtered_data)
        return df if fmt == "dataframe" else df.to_dict(orient="records")

    async def save(self, basepath: Path, prefix: str = "", ts_range: tuple[int | float, int | float] | None = None, **kwargs) -> Path:
        """Save collected stats to a DataFrame and optionally to a CSV file if data_dir is set."""
        stats: pd.DataFrame = await self.export(ts_range, fmt="dataframe", **kwargs)
        summary: pd.DataFrame = await self.summarize(fmt="dataframe", **kwargs)
        logs = pd.DataFrame(self.logs, columns=["log"])
        if prefix:
            basepath = Path(basepath) / prefix
        statspath = safe_path(basepath / "stats.csv")
        summarypath = safe_path(basepath / "summary.csv")
        logspath = safe_path(basepath / "logs.csv")
        stats.to_csv(statspath, index=False)
        summary.to_csv(summarypath, index=True, index_label="metric")
        logs.to_csv(logspath, index=False)
        logging.info("Statistics saved to %s.", basepath)
        return basepath