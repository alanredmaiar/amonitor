# docker-monitor
An asynchronous docker monitor and statistics collector for python


# Creating the README.md file with the provided content
readme_content = """
# Multipurpose Monitoring Library - `amonitor`

## Overview

`amonitor` is a Python library designed for multipurpose resource monitoring across various platforms and environments. While the library is intended to support a wide range of monitoring tasks, it is currently under active development. At this stage, `amonitor` provides robust asynchronous monitoring capabilities specifically for Docker containers. However, the architecture is being designed to accommodate future extensions, making it a versatile tool for monitoring other services and systems in the future.

## Features

- **Multipurpose Design**: Aiming to support a variety of monitoring tasks across different platforms (currently focused on Docker).
- **Asynchronous Monitoring**: Utilizes `asyncio` for efficient, non-blocking monitoring of Docker containers.
- **Flexible Filtering**: Filter Docker containers by name and port for targeted monitoring.
- **Resource Aggregation**: Aggregates resource usage metrics for detailed analysis.
- **Data Export**: Export monitored data to CSV files or Pandas DataFrames.
- **Context Management**: Easy start/stop of monitoring using Python's context managers.

## Installation

To get started with `amonitor`, you can install it via `poetry`:

```bash
poetry add amonitor