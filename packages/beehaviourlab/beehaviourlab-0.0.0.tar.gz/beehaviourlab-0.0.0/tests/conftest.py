"""Configuration file for pytest."""

import pytest

# Configure pytest
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path_factory):
    """Create a temporary directory with sample data files."""
    data_dir = tmp_path_factory.mktemp("sample_data")
    return data_dir


@pytest.fixture
def cleanup_files():
    """Fixture to ensure test files are cleaned up."""
    files_to_cleanup = []

    def register_file(filepath):
        files_to_cleanup.append(filepath)

    yield register_file

    # Cleanup
    for filepath in files_to_cleanup:
        if filepath.exists():
            filepath.unlink()
