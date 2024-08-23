
# `amonitor` - Asynchronous Monitoring Library

`amonitor` is a multipurpose, asynchronous monitoring library designed to support a variety of resource monitoring tasks. Although the library is currently under development and focuses on Docker container monitoring, it is built with the flexibility to extend monitoring capabilities to other resources in the future.

## Features

- **Asynchronous Monitoring:** Perform monitoring tasks asynchronously to ensure non-blocking operations.
- **Docker Container Monitoring:** Retrieve and analyze Docker container statistics such as CPU, memory, network, and disk usage.
- **Customizable and Extendable:** While currently focused on Docker, `amonitor` is designed to be extended for other monitoring purposes.
- **Data Aggregation and Summarization:** Aggregate and summarize collected statistics for easier analysis.
- **Data Export:** Export monitoring data to CSV files or pandas DataFrames for further analysis.

## Installation

`amonitor` can be installed via Poetry. Clone the repository and install the dependencies:

```bash
git clone https://github.com/your-username/amonitor.git
cd amonitor
poetry install
```

## Usage

Here are some examples of how to use the `amonitor` library:

### 1. List All Running Docker Containers

```python
import asyncio
from amonitor.docker import DockerMonitor

async def list_containers():
    monitor = DockerMonitor()
    containers = await monitor.list_containers()
    print("Running containers:", containers)

asyncio.run(list_containers())
```

### 2. Monitor a Docker Container

To monitor a Docker container asynchronously and collect statistics:

```python
import asyncio
from amonitor.docker import DockerMonitor

async def monitor_container():
    monitor = DockerMonitor(container_name="your_container_name")
    async with monitor.monitor():
        await asyncio.sleep(10)  # Adjust sleep duration for desired monitoring time
    print("Summary:", monitor.summary)
    print("Aggregated Stats:", monitor.aggregated_stats)

asyncio.run(monitor_container())
```

### 3. Export Collected Data

After collecting data, you can export it to CSV files:

```python
import asyncio
from pathlib import Path
from amonitor.docker import DockerMonitor

async def export_data():
    monitor = DockerMonitor(container_name="your_container_name")
    async with monitor.monitor():
        await asyncio.sleep(10)  # Collect data for 10 seconds
    basepath = Path("/path/to/save/data")
    await monitor.save(basepath=basepath, prefix="docker_monitor")

asyncio.run(export_data())
```

### 4. Filtering Data by Timestamp Range

You can filter the collected data by a timestamp range for more specific analysis:

```python
import asyncio
from amonitor.docker import DockerMonitor

async def summarize_data():
    monitor = DockerMonitor(container_name="your_container_name")
    async with monitor.monitor():
        await asyncio.sleep(10)
    
    # Assuming timestamps are in UNIX format
    ts_range = (start_timestamp, end_timestamp)
    summary = await monitor.summarize(ts_range=ts_range)
    print("Filtered Summary:", summary)

asyncio.run(summarize_data())
```

## Development Status

`amonitor` is currently under development. The primary focus is on Docker container monitoring, but the architecture is designed to support a wide range of monitoring functionalities in the future.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to help improve `amonitor`. Please follow the standard conventions for Python libraries.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, please reach out to the project maintainers at `your.email@example.com`.

---

This documentation provides an overview of the `amonitor` library, its current capabilities, and examples of how to use it for Docker container monitoring. As the library evolves, the documentation will be updated to reflect new features and capabilities.