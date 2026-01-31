"""Root test fixtures for amsdal_crm."""

from enum import Enum
from typing import Any

import pytest


class DatabaseBackend(Enum):
    SQLITE = 'sqlite'
    POSTGRES = 'postgres'


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        '--database_backend',
        action='store',
        default=DatabaseBackend.SQLITE.value,
        help='Backend to use for lakehouse (sqlite-historical or postgres-historical)',
    )


@pytest.fixture(scope='session')
def database_backend(request: Any) -> DatabaseBackend:
    backend_str = request.config.getoption('--database_backend')
    return DatabaseBackend(backend_str)
