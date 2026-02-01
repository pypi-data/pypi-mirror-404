import pytest

from evakit.logging_utils import setup_root_logger

__all__ = ["configure_logging"]


@pytest.fixture(autouse=True, scope="session")
def configure_logging():
    """Configure logging for all tests."""
    setup_root_logger(process_info=True)
