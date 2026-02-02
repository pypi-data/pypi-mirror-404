from os import getenv

from build_cub import METADATA


def test_config_works() -> None:
    """Test to ensure the env was set"""
    assert getenv(METADATA.env_variable) == "test", "Environment variable not set correctly"


def test_metadata() -> None:
    """Test to ensure metadata is correctly set."""
    assert METADATA.name == "build-cub", "Metadata name does not match"
    # assert METADATA.version != "0.0.0", f"Version should not be '0.0.0': {METADATA.version}:{METADATA.version_tuple}"
    assert METADATA.description != "No description available.", "Metadata description should not be empty"
    assert METADATA.project_name == "build_cub", "Project name does not match"
