"""
Adapter package exports.

The optional dependencies (torch, tensorflow, jax) may not be
installed in every environment. We try to import the adapters
and fall back to sentinel values when the dependency is missing.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from .pytorch_adapter import PyTorchAdapter  # noqa: F401
except Exception as exc:  # pragma: no cover - optional dependency
    PyTorchAdapter = None  # type: ignore[assignment]
    logger.debug("PyTorch adapter unavailable: %s", exc)

try:
    from .tensorflow_adapter import TensorFlowAdapter  # noqa: F401
except Exception as exc:  # pragma: no cover - optional dependency
    TensorFlowAdapter = None  # type: ignore[assignment]
    logger.debug("TensorFlow adapter unavailable: %s", exc)

try:
    from .jax_adapter import JAXAdapter  # noqa: F401
except Exception as exc:  # pragma: no cover - optional dependency
    JAXAdapter = None  # type: ignore[assignment]
    logger.debug("JAX adapter unavailable: %s", exc)

__all__ = [
    "PyTorchAdapter",
    "TensorFlowAdapter",
    "JAXAdapter",
]

