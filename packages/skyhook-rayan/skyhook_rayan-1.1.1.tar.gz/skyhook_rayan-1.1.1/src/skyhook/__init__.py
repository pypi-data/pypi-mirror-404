"""Skyhook - Secure file server with upload capabilities."""

__version__ = "1.0.0"
__author__ = "Skyhook Contributors"
__description__ = "A secure, zero-config CLI file server with upload capabilities and encrypted transport"

from .main import app as cli_app
from .server import create_app

__all__ = ["cli_app", "create_app", "__version__"]