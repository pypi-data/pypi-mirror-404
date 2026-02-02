"""Tests suite for `build_cub`."""

from os import environ
from pathlib import Path

from build_cub import METADATA

TESTS_DIR: Path = Path(__file__).parent
TMP_DIR: Path = TESTS_DIR / "tmp"
FIXTURES_DIR: Path = TESTS_DIR / "fixtures"
TEST_TOML_PATH: Path = FIXTURES_DIR / "test_bear_build.toml"
MAIN_CONFIG_PATH = Path("bear_build.toml")

environ[f"{METADATA.env_variable}"] = "test"
