"""
Framework Detector
Automatically detects which ML framework is being used
"""

import sys
import logging

logger = logging.getLogger(__name__)


class FrameworkDetector:
    """Detect ML framework (PyTorch/TensorFlow/JAX)"""
    
    def detect(self) -> str:
        """
        Detect which framework is imported
        Returns: 'pytorch', 'tensorflow', 'jax', or 'unknown'
        """
        
        # Check for PyTorch
        if 'torch' in sys.modules:
            logger.info("Detected PyTorch")
            return 'pytorch'
        
        # Check for TensorFlow
        if 'tensorflow' in sys.modules:
            logger.info("Detected TensorFlow")
            return 'tensorflow'
        
        # Check for JAX
        if 'jax' in sys.modules:
            logger.info("Detected JAX")
            return 'jax'
        
        logger.warning("No ML framework detected")
        return 'unknown'
