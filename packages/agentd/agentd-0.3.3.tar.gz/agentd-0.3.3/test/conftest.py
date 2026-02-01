"""
Pytest configuration and fixtures.
"""
import pytest
from dotenv import load_dotenv


def pytest_configure(config):
    """Load .env file before running tests."""
    load_dotenv()
