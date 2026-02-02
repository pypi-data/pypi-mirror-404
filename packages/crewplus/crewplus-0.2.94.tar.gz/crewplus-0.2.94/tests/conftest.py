"""
Pytest configuration for crewplus-base tests.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may call external APIs)"
    )
