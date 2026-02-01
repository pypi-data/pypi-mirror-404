"""
CloudBrain Server - AI Collaboration Platform Server

This package provides the CloudBrain server for AI agent collaboration.
"""

__version__ = "1.0.0"

from .cloud_brain_server import CloudBrainEnhanced as CloudBrainServer

__all__ = [
    "CloudBrainServer",
    "__version__",
]
