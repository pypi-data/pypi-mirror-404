"""
JAX Adapter

Minimal placeholder for JAX-based monitoring so that the package can be
built without requiring JAX at install time.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import jax  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    jax = None  # type: ignore[assignment]


class JAXAdapter:
    """No-op JAX adapter placeholder."""

    def __init__(self, exporter, config: Dict[str, Any]):
        if jax is None:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "JAX is not installed. Install the 'jax' extra to enable JAX monitoring. "
                "e.g. pip install onex-sdk[jax]"
            )
        self.exporter = exporter
        self.config = config
        logger.info("JAX monitoring is experimental.")

    def attach_monitoring(self, model):
        """
        Attach monitoring hooks to a JAX model.
        Currently returns the model unchanged and logs the limitation.
        """
        logger.warning("JAXAdapter.attach_monitoring is a placeholder.")
        return model

    def cleanup(self):
        """Perform any cleanup required by the adapter."""
        logger.debug("JAXAdapter cleanup complete.")

