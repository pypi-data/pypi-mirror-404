"""
OneX SDK
Framework-agnostic neural signal monitoring

Usage:
    from onex import OneXMonitor
    
    monitor = OneXMonitor(api_key="your-key")
    model = monitor.watch(model)  # Framework automatically detected!
"""

from .core import OneXMonitor
from .version import __version__

__all__ = ['OneXMonitor', '__version__']
