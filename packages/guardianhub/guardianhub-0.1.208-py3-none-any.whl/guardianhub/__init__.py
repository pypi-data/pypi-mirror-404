"""GuardianHub SDK - Unified SDK for Local AI Guardian

This package provides core functionality for the GuardianHub platform,
including logging, metrics, and FastAPI utilities.
"""

# Version
from ._version import __version__  # version exported for users
# Core functionality
from .logging import get_logger, setup_logging
from .utils.fastapi_utils import initialize_guardian_app

# Public API
__all__ = [
    # Version
    "__version__",
    
    # Logging
    "get_logger",
    "initialize_guardian_app"
]