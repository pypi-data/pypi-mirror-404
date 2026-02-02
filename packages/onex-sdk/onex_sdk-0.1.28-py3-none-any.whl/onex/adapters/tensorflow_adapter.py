"""
TensorFlow Adapter

Provides a minimal implementation that can be extended to capture
signals from TensorFlow models. The adapter is optional and only
activates when TensorFlow is installed and detected.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import tensorflow as tf  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tf = None  # type: ignore[assignment]


class TensorFlowAdapter:
    """No-op TensorFlow adapter placeholder."""

    def __init__(self, exporter, config: Dict[str, Any]):
        if tf is None:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "TensorFlow is not installed. Install the 'tensorflow' extra to enable "
                "TensorFlow monitoring. e.g. pip install onex-sdk[tensorflow]"
            )
        self.exporter = exporter
        self.config = config
        self._hooks = []
        logger.info("TensorFlow monitoring is experimental.")

    def attach_monitoring(self, model):
        """
        Attach monitoring hooks to a TensorFlow model.
        Currently we return the model unchanged and log that monitoring
        is not yet implemented.
        """
        logger.warning("TensorFlowAdapter.attach_monitoring is a placeholder.")
        return model

    def cleanup(self):
        """Remove hooks if any were registered."""
        self._hooks.clear()
        logger.debug("TensorFlowAdapter cleanup complete.")

