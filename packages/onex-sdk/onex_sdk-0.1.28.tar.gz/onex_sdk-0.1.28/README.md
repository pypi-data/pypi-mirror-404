# OneX Observability SDK

The OneX SDK provides framework-agnostic utilities to monitor neural
signals and export them to the OneX observability platform. It detects
popular machine learning frameworks (PyTorch, TensorFlow, JAX) and
attaches lightweight instrumentation to running models.

## Installation

```bash
pip install onex-sdk
```

Optional extras are available for framework-specific monitoring:

```bash
# PyTorch support
pip install onex-sdk[pytorch]

# TensorFlow support
pip install onex-sdk[tensorflow]

# JAX support
pip install onex-sdk[jax]
```

## Quick Start

```python
from onex import OneXMonitor

monitor = OneXMonitor(api_key="your-api-key")
model = monitor.watch(model)
```

## Development

Create a virtual environment and install the development requirements:

```bash
pip install -r requirements-dev.txt
```

Then run the tests with `pytest`.

