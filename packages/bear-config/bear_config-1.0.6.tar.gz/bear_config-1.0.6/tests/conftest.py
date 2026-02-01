"""Configuration for the pytest test suite."""

from os import environ

from bear_config import METADATA

environ[f"{METADATA.env_variable}"] = "test"
